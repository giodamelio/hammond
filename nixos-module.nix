{
  config,
  lib,
  ...
}: let
  cfg = config.services.hammond;
in {
  options.services.hammond = {
    enable = lib.mkEnableOption "Hammond automation service";

    package = lib.mkOption {
      type = lib.types.package;
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
}
