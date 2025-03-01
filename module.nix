localPkgs:

{ config, lib, pkgs, ... }:

with lib;
let
  cfg = config.fudo.summarizer;

  summarizer = localPkgs."${pkgs.system}";
in {
  options.fudo.summarizer = with types; {
    enable = mkEnableOption "Add summarizer to the system.";

    ollamaServer = mkOption {
      type = str;
      description = "URL of the Ollama server to use, including port.";
      example = "https://ollama.domain.com:11434";
    };

    model = mkOption {
      type = str;
      description = "Name of model to use for summarization.";
    };

    chunkSize = mkOption {
      type = str;
      description =
        "Size of chunks into which to break text documents for processing, in tokens.";
      default = 2048;
    };

    chunkOverlap = mkOption {
      type = str;
      description =
        "Number of tokens for which the chunks should overlap, for shared context.";
      default = 256;
    };
  };

  config = let
    summarizerWithParams = pkgs.writeShellApplication {
      name = "summarize";

      text = concatStringsSep " " [
        "${summarizer}/bin/summarizer"
        "--server ${cfg.ollamaServer}"
        "--model ${cfg.model}"
        "--chunk_size ${toString cfg.chunkSize}"
        "--overlap ${toString cfg.chunkOverlap}"
        "$@"
      ];
    };
  in {
    environment.systemPackages = optionals cfg.enable [ summarizerWithParams ];
  };
}
