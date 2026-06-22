{
    inputs = {
        nixpkgs.url = "https://flakehub.com/f/NixOS/nixpkgs/*.tar.gz";
        n64 = {
            url = "github:glankk/n64";
            flake = false;
        };
        rust-overlay = {
            url = "github:oxalica/rust-overlay";
            inputs.nixpkgs.follows = "nixpkgs";
        };
    };
    outputs = attrs: let
        supportedSystems = [
            "aarch64-darwin"
            "aarch64-linux"
            "x86_64-darwin"
            "x86_64-linux"
        ];
        forEachSupportedSystem = f: attrs.nixpkgs.lib.genAttrs supportedSystems (system: f {
            crossPkgs = import attrs.nixpkgs {
                crossSystem = "mips64-elf";
                localSystem = system;
            };
            pkgs = import attrs.nixpkgs {
                inherit system;
                overlays = [
                    attrs.rust-overlay.overlays.default # required for cargo-script
                ];
            };
        });
    in {
        devShells = forEachSupportedSystem ({ crossPkgs, pkgs, ... }: {
            default = pkgs.mkShell {
                CPATH = "${attrs.n64}/include";
                packages = with pkgs; [
                    armips # required to build asm
                    crossPkgs.buildPackages.gcc # required to build C
                    gnumake # required to build asm/C
                    rust-bin.nightly.latest.default # nightly cargo, required to run assets/git-merge-pr.rs
                    (python3.withPackages (python-pkgs: with python-pkgs; [ # required to build asm/C and for the deploy script
                        docopt # required for update-presets.py
                        requests # required for the deploy script
                    ]))
                ];
            };
        });
    };
}
