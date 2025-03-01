{
  inputs = {
    nixpkgs.url = "nixpkgs/nixos-24.11";
    utils.url = "github:numtide/flake-utils";
  };

  outputs = { self, nixpkgs, utils, ... }:
    utils.lib.eachDefaultSystem (system:
      let pkgs = nixpkgs.legacyPackages."${system}";
      in {
        packages = { summarizer = pkgs.callPackage ./summarizer.nix { }; };

        devShells = {
          default = pkgs.mkShell {
            buildInputs = [ self.packages."${system}".summarizer ];
          };
        };
      }) // {
        nixosModules = rec {
          default = summarizer;
          summarizer = {
            overlays = [ self.overlays.summarizer ];
            imports = [ ./nix.module ];
            config.nixpkgs.overlays = [ self.overlays.summarizer ];
          };
        };

        overlays = rec {
          default = summarizer;
          summarizer = final: prev: {
            inherit (self.packages."${prev.system}") summarizer;
          };
        };
      };
}
