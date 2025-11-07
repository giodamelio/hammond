{ pkgs, lib, config, inputs, ... }:

{
  packages = with pkgs; [ restate ];

  languages.go = {
    enable = true;
  };

  dotenv.enable = true;
}
