{
  description = "Multipurpose automation for life";

  inputs = {
    # Pinned to same revision as NixOS config to use cached restate build
    # TODO: Set up our own binary cache server for unfree packages
    nixpkgs.url = "github:NixOS/nixpkgs/d5faa84122bc0a1fd5d378492efce4e289f8eac1";
    flake-parts.url = "github:hercules-ci/flake-parts";
    pyproject-nix = {
      url = "github:pyproject-nix/pyproject.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    uv2nix = {
      url = "github:pyproject-nix/uv2nix";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    pyproject-build-systems = {
      url = "github:pyproject-nix/build-system-pkgs";
      inputs.pyproject-nix.follows = "pyproject-nix";
      inputs.uv2nix.follows = "uv2nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    git-hooks = {
      url = "github:cachix/git-hooks.nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    mcp-servers-nix = {
      url = "github:natsukium/mcp-servers-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
  };

  outputs = inputs @ {flake-parts, ...}:
    flake-parts.lib.mkFlake {inherit inputs;} {
      imports = [
        inputs.treefmt-nix.flakeModule
        inputs.git-hooks.flakeModule
      ];

      systems = [
        "x86_64-linux"
        "aarch64-linux"
        "aarch64-darwin"
        "x86_64-darwin"
      ];

      flake = {
        nixosModules.default = import ./nixos-module.nix;
      };

      perSystem = {
        config,
        self',
        inputs',
        pkgs,
        system,
        ...
      }: let
        inherit (pkgs) lib;

        # Python Stuff
        python = pkgs.python3;
        workspace = inputs.uv2nix.lib.workspace.loadWorkspace {workspaceRoot = ./.;};
        overlay = workspace.mkPyprojectOverlay {
          sourcePreference = "wheel";
        };
        editableOverlay = workspace.mkEditablePyprojectOverlay {
          root = "$REPO_ROOT";
        };
        pyprojectPackages = pkgs.callPackage inputs.pyproject-nix.build.packages {
          inherit python;
        };
        pythonSet =
          pyprojectPackages.overrideScope
          (
            lib.composeManyExtensions [
              inputs.pyproject-build-systems.overlays.wheel
              overlay
            ]
          );
        pythonSetEditable =
          pyprojectPackages.overrideScope
          (
            lib.composeManyExtensions [
              inputs.pyproject-build-systems.overlays.wheel
              overlay
              editableOverlay
            ]
          );
        virtualenv = pythonSet.mkVirtualEnv "hammond-env" workspace.deps.default;
        virtualenvEditable = pythonSetEditable.mkVirtualEnv "hammond-dev-env" workspace.deps.all;
        pyprojectBuildUtils = pkgs.callPackage inputs.pyproject-nix.build.util {};

        # MCP server that allows access to our LSP
        mcpLanguageServer = pkgs.buildGoModule rec {
          pname = "mcp-language-server";
          version = "0.1.1";

          src = pkgs.fetchFromGitHub {
            owner = "isaacphi";
            repo = "mcp-language-server";
            rev = "v${version}";
            hash = "sha256-T0wuPSShJqVW+CcQHQuZnh3JOwqUxAKv1OCHwZMr7KM=";
          };

          vendorHash = "sha256-3NEG9o5AF2ZEFWkA9Gub8vn6DNptN6DwVcn/oR8ujW0=";

          ldflags = ["-s" "-w"];

          # Skip the tests
          doCheck = false;
          excludedPackages = ["integrationtests"];

          meta = {
            description = "Mcp-language-server gives MCP enabled clients access semantic tools like get definition, references, rename, and diagnostics";
            homepage = "https://github.com/isaacphi/mcp-language-server";
            license = lib.licenses.bsd3;
            maintainers = with lib.maintainers; [];
            mainProgram = "mcp-language-server";
          };
        };

        # Generate our MCP config
        mcpConfig = inputs.mcp-servers-nix.lib.mkConfig pkgs {
          format = "json";
          fileName = ".mcp.json";
          programs = {
            git.enable = true;
            context7.enable = true;
          };
          settings.servers = {
            restate-docs = {
              type = "http";
              url = "https://docs.restate.dev/mcp";
            };
            language-server = {
              type = "stdio";
              command = lib.getExe mcpLanguageServer;
              args = [
                "--workspace"
                "."
                "--lsp"
                "basedpyright-langserver"
                "--"
                "--stdio"
              ];
            };
          };
        };
      in {
        # Allow some unfree packages
        _module.args.pkgs = import inputs.nixpkgs {
          inherit system;
          config.allowUnfreePredicate = pkg:
            builtins.elem (pkgs.lib.getName pkg) [
              "restate"
            ];
        };

        # Development shell
        devShells.default = pkgs.mkShell {
          inputsFrom = [
            config.pre-commit.devShell
            config.treefmt.build.devShell
          ];

          packages = with pkgs; [
            # Development tools
            restate
            nil
            nix-output-monitor
            virtualenvEditable
            uv
            basedpyright
          ];

          env = {
            UV_NO_SYNC = "1";
            UV_PYTHON = pythonSetEditable.python.interpreter;
            UV_PYTHON_DOWNLOADS = "never";
          };

          shellHook = ''
            unset PYTHONPATH
            export REPO_ROOT=$(git rev-parse --show-toplevel)

            # Symlink in the .mcp.json
            ln -sf ${mcpConfig} ./.mcp.json
          '';
        };

        # Treefmt configuration
        treefmt = {
          projectRootFile = "flake.nix";
          programs = {
            alejandra.enable = true; # Nix formatter
            ruff-format.enable = true; # Python formatter
          };
        };

        # Git hooks configuration
        pre-commit = {
          check.enable = true;
          settings = {
            enable = true;
            default_stages = [
              "pre-commit"
              "pre-push"
            ];
            hooks = {
              # Formatting
              treefmt = {
                enable = true;
                package = config.treefmt.build.wrapper;
              };

              # Python stuff
              uv-check.enable = true;
              ruff.enable = true;
              mypy = {
                enable = true;
                entry = lib.mkForce "uv run mypy";
              };
              pyright = {
                enable = true;
                # Make sure the pyright from Nixpkgs knows about our local dependencies
                entry = lib.mkForce "${pkgs.writeShellScript "pyright-wrapper" ''
                  export PYTHONPATH=${virtualenvEditable}/lib/python3.13/site-packages:$PYTHONPATH
                  exec ${pkgs.pyright}/bin/pyright "$@"
                ''}";
              };

              # Random ones
              end-of-file-fixer.enable = true;
              trim-trailing-whitespace.enable = true;
            };
          };
        };

        packages = {
          default = pyprojectBuildUtils.mkApplication {
            venv = virtualenv;
            package = pythonSet.hammond;
          };
        };
      };
    };
}
