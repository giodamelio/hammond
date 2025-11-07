{
  description = "Multipurpose automation for life";

  inputs = {
    # Pinned to same revision as NixOS config to use cached restate build
    # TODO: Set up our own binary cache server for unfree packages
    nixpkgs.url = "github:NixOS/nixpkgs/d5faa84122bc0a1fd5d378492efce4e289f8eac1";
    flake-parts.url = "github:hercules-ci/flake-parts";
    treefmt-nix = {
      url = "github:numtide/treefmt-nix";
      inputs.nixpkgs.follows = "nixpkgs";
    };
    git-hooks = {
      url = "github:cachix/git-hooks.nix";
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

      perSystem = {
        config,
        self',
        inputs',
        pkgs,
        system,
        ...
      }: let
        hammond = pkgs.buildGoModule {
          pname = "hammond";
          version = "0.1.0";
          src = ./.;
          # vendorHash = pkgs.lib.fakeHash;
          vendorHash = null;
          buildInputs = [];
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

        # Main package
        packages = {
          default = hammond;
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
          ];

          shellHook = ''
            echo
            echo "Hammond Development Environment"
            echo "Available commands:"
            echo "  treefmt             - Format all code files"
            echo
          '';
        };

        # Treefmt configuration
        treefmt = {
          projectRootFile = "flake.nix";
          programs = {
            alejandra.enable = true; # Nix formatter
            gofmt.enable = true; # Go formatter
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

              # Golang stuff
              gotest.enable = true;
              revive.enable = true;

              # Random ones
              end-of-file-fixer.enable = true;

              trim-trailing-whitespace.enable = true;
            };
          };
        };
      };
    };
}
