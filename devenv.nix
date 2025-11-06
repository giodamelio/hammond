{ pkgs, lib, config, inputs, ... }:

{
  packages = with pkgs; [ restate ];

  languages.python = {
    enable = true;
    uv.enable = true;
  };

  dotenv.enable = true;
}
