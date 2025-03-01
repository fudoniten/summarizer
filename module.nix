{ config, lib, pkgs, ... }:

with lib; {
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

      runtimeInputs = [ summarizer ];

      text = concatStringsSep " " [
        "${summarizer}/bin/summarizer"
        "--server ${cfg.ollamaServer}"
        "--model ${cfg.model}"
        "$@"
      ];
    };
  in { environment.systemPackages = [ summarizerWithParams ]; };
}
