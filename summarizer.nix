{ lib, python3Packages, ... }:

python3Packages.buildPythonPackage rec {
  pname = "summarizer";
  version = "0.1.0";

  src = ./.;

  propagatedBuildInputs = with python3Packages; [
    langchain
    langchain-community
    ollama
    pytorch
    transformers
  ];

  installPhase = ''
    mkdir -p $out/bin
    cp ./summarizer/summarizer.py $out/bin/summarizer
    chmod +x $out/bin/summarizer
  '';

  meta = with lib; {
    description =
      "Summarize text documents according to instructions with ollama.";
    license = licenses.mit;
  };
}
