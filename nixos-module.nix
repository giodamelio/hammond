{self, ...}: {
  flake.nixosModules.default = {
    config,
    lib,
    pkgs,
    ...
  }: let
    cfg = config.services.hammond;
  in {
    options.services.hammond = {
      enable = lib.mkEnableOption "Hammond automation service";

      package = lib.mkOption {
        type = lib.types.package;
        default = self.packages.${pkgs.stdenv.system}.default;
        defaultText = lib.literalExpression "pkgs.hammond";
        description = "The hammond package to use";
      };
    };

    config = lib.mkIf cfg.enable {
      systemd.services.hammond = {
        description = "Hammond automation service";
        wantedBy = ["multi-user.target"];
        after = ["network-online.target"];
        wants = ["network-online.target"];

        serviceConfig = {
          ExecStart = "${lib.getExe cfg.package}";
          Restart = "always";
          RestartSec = "10s";

          # Security hardening
          DynamicUser = true;
          CacheDirectory = "hammond";
          PrivateTmp = true;
          ProtectSystem = "strict";
          ProtectHome = true;
          NoNewPrivileges = true;
          PrivateDevices = true;
          ProtectKernelTunables = true;
          ProtectKernelModules = true;
          ProtectControlGroups = true;
          RestrictSUIDSGID = true;
        };
      };
    };
  };
}
