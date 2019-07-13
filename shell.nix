{ pkgs ? import <nixpkgs> {} }:

with pkgs;

let
  thePythonPackages = pkgs.python37Packages;

  urlmatch = thePythonPackages.buildPythonPackage rec {
    pname = "urlmatch";
    version = "1.0.1";
    name = "${pname}-${version}";
    src = thePythonPackages.fetchPypi {
      inherit pname version;
      sha256 = "0bgb2snkc5jv6nngdxv1pwa5gzqjcm7f8z2lqkpk2frzy0lka31z";
    };
    doCheck = false;
  };
in

stdenv.mkDerivation {
  name = "userscript-proxy";
  buildInputs = [
    mitmproxy
    mypy
    (with thePythonPackages; [
      beautifulsoup4 urlmatch lxml
    ])
  ];
}
