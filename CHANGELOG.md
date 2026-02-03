# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/)
and this project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

<!-- insertion marker -->
## [v2.9.3](https://github.com/farrokhi/dnsdiag/releases/tag/v2.9.3) - 2026-02-03

<small>[Compare with v2.9.2](https://github.com/farrokhi/dnsdiag/compare/v2.9.2...v2.9.3)</small>

### Added

- Add explanation of DNSSEC flags and EDE codes in dnsping output (#155) ([81c50bc](https://github.com/farrokhi/dnsdiag/commit/81c50bc3be7aa82e264a4f13d3f1ef09399b59b0) by [@jeremyrayjewell](https://github.com/jeremyrayjewell)).
- Add mutual exclusivity to command line parameters (#156) ([21a6a3b](https://github.com/farrokhi/dnsdiag/commit/21a6a3bb1dbbb3e61bd29b9575de86ca2ff44ed1) by [@farrokhi](https://github.com/farrokhi)).

### Fixed

- fix(dnstraceroute): handle expected network errors during TCP traceroute ([6950488](https://github.com/farrokhi/dnsdiag/commit/69504884e8d0f585c1ce0f579f64e824d3856670) by [@farrokhi](https://github.com/farrokhi)).
- fix(dnstraceroute): enable TTL control for QUIC and HTTP/3 protocols (#157) ([d2ba23c](https://github.com/farrokhi/dnsdiag/commit/d2ba23ca1c681a21113704384b8a6c7cebe735eb) by [@farrokhi](https://github.com/farrokhi)).
- fix: remove Windows ARM64 from CI build matrix ([04f8b62](https://github.com/farrokhi/dnsdiag/commit/04f8b6243fdf803538e2bcea85faee386434be9a) by [@farrokhi](https://github.com/farrokhi)).
- fix: replace unreliable dnspython timing with perf_counter measurements ([0a3a5f6](https://github.com/farrokhi/dnsdiag/commit/0a3a5f6a723a71ec65a5be47cfb83001899d3262) by [@farrokhi](https://github.com/farrokhi)).
- fix: improved error handling for DoH, DoH3 and DoQ ([6d14c1f](https://github.com/farrokhi/dnsdiag/commit/6d14c1f78fa9715e4c962d829f38f8472c43ad42) by [@farrokhi](https://github.com/farrokhi)).
- fix: treat connection refused as transient across all DNS protocols ([099d627](https://github.com/farrokhi/dnsdiag/commit/099d627b4c683682f712ba5c749ff6ca2fc80185) by [@farrokhi](https://github.com/farrokhi)).
- fix: handle transient QUIC connection failures gracefully ([87b2285](https://github.com/farrokhi/dnsdiag/commit/87b2285149c23b9758d332ef811c1970e407f2d6) by [@farrokhi](https://github.com/farrokhi)).
- fix: detect Windows ARM64 architecture correctly in build script ([19f3dc2](https://github.com/farrokhi/dnsdiag/commit/19f3dc2eebc3da8c29dde26df09fe593c6b63aa2) by [@farrokhi](https://github.com/farrokhi)).

<!-- insertion marker -->
## [v2.9.2](https://github.com/farrokhi/dnsdiag/releases/tag/v2.9.2) - 2026-01-13

<small>[Compare with v2.9.1](https://github.com/farrokhi/dnsdiag/compare/v2.9.1...v2.9.2)</small>

### Fixed

- fix: add missing import to unbreak tests ([b3ca60a](https://github.com/farrokhi/dnsdiag/commit/b3ca60a8924317264f8fdd579dbc6cfa20fb023b) by [@farrokhi](https://github.com/farrokhi)).
- fix: output valid JSONL instead of concatenated JSON objects ([7b3f55c](https://github.com/farrokhi/dnsdiag/commit/7b3f55c7dbb81cb8d4b261572f1417b9982f9c53) by [@farrokhi](https://github.com/farrokhi)).
- fix: use bytes for NSID EDNS option instead of string ([4bccff6](https://github.com/farrokhi/dnsdiag/commit/4bccff67968fae72d63dff446fcf767bb6d969d5) by [@farrokhi](https://github.com/farrokhi)).
- fix: show first answer with record type in -a flag output ([076d81f](https://github.com/farrokhi/dnsdiag/commit/076d81fd952689d63ea29451d943078e6c32db7c) by [@farrokhi](https://github.com/farrokhi)).
- fix: tests now use sys.executable instead of playing python roulette ([9a85033](https://github.com/farrokhi/dnsdiag/commit/9a85033573816722f6f1cd405eb55fb202f8eced) by [@farrokhi](https://github.com/farrokhi)).
- fix: survive network status changes instead of dying ([42e520a](https://github.com/farrokhi/dnsdiag/commit/42e520a1bd6a877d69611a61d9f71412c0ee1ed3) by [@farrokhi](https://github.com/farrokhi)).
- fix: return exit code 0 for --help flag ([4ecf76a](https://github.com/farrokhi/dnsdiag/commit/4ecf76af24bba1369aa05a906f2a98af949d3cef) by [@farrokhi](https://github.com/farrokhi)).
- fix: install virtualenv dependency in build release workflow ([204a256](https://github.com/farrokhi/dnsdiag/commit/204a2567ac18756e16a6542a639ecc4a0f83ad11) by [@farrokhi](https://github.com/farrokhi)).
- fix: handle dependency installation failures and relax cryptography constraint ([4a7575e](https://github.com/farrokhi/dnsdiag/commit/4a7575e4fb19921387b912975f589b8f8a2de3e0) by [@farrokhi](https://github.com/farrokhi)).
- fix: handle network restrictions on ARM64 GitHub Actions runners ([c2df8a9](https://github.com/farrokhi/dnsdiag/commit/c2df8a9688b86ff684912db3dbd3fc218713623c) by [@farrokhi](https://github.com/farrokhi)).
- fix: exclude Python 3.10 and 3.13 from Windows ARM64 runners ([524cfbf](https://github.com/farrokhi/dnsdiag/commit/524cfbf261bb167441e810184db18c8fcd266011) by [@farrokhi](https://github.com/farrokhi)).
- fix: prevent negative sleep duration in interruptible sleep loop ([6bc00ab](https://github.com/farrokhi/dnsdiag/commit/6bc00ab5202e22719252bb27d3c89d6fd3e57dab) by [@farrokhi](https://github.com/farrokhi)).

## [v2.9.1](https://github.com/farrokhi/dnsdiag/releases/tag/v2.9.1) - 2025-10-31

<small>[Compare with v2.9.0](https://github.com/farrokhi/dnsdiag/compare/v2.9.0...v2.9.1)</small>

### Fixed

- fix: truncate cookie display in normal mode to 8 characters ([6d8f609](https://github.com/farrokhi/dnsdiag/commit/6d8f6098cdf666bd2cbf6ad5805bafdabec99cb3) by [@farrokhi](https://github.com/farrokhi)).
- fix: include root-level Python modules in package distribution ([0470053](https://github.com/farrokhi/dnsdiag/commit/047005321125a5393eebdb0f24e792e07e85cde3) by [@farrokhi](https://github.com/farrokhi)).

## [v2.9.0](https://github.com/farrokhi/dnsdiag/releases/tag/v2.9.0) - 2025-10-26

<small>[Compare with v2.8.1](https://github.com/farrokhi/dnsdiag/compare/v2.8.1...v2.9.0)</small>

### Added

- Add --nsid support to dnstraceroute (#153) ([85d96f6](https://github.com/farrokhi/dnsdiag/commit/85d96f66d2cfa36d5fd47d2fb5022f269e23aecb) by [@farrokhi](https://github.com/farrokhi)).
- Add tests for cookie feature in dnsping ([66b4faa](https://github.com/farrokhi/dnsdiag/commit/66b4faa80fbf8b2cbe94e8f73e942400715a40ef) by [@farrokhi](https://github.com/farrokhi)).
- Add support for Python 3.14 ([8099260](https://github.com/farrokhi/dnsdiag/commit/8099260c69d159844c2790bdd0064e943c847e03) by [@farrokhi](https://github.com/farrokhi)).
- Add marker to disable IPv6 tests on Github Action ([a756d10](https://github.com/farrokhi/dnsdiag/commit/a756d10bc22b57ad00273200528b1955c73271f0) by [@farrokhi](https://github.com/farrokhi)).
- Add Windows to test suite ([1e1cbdb](https://github.com/farrokhi/dnsdiag/commit/1e1cbdb5f745a67bddaabf9cc83da5b755115f7b) by [@farrokhi](https://github.com/farrokhi)).
- Add GitHub Actions workflow for running pytest integration tests ([4f4021c](https://github.com/farrokhi/dnsdiag/commit/4f4021c0fd51ce36017dee0884ec44cdc3981e08) by [@farrokhi](https://github.com/farrokhi)).
- Add type checking to tests ([93324be](https://github.com/farrokhi/dnsdiag/commit/93324beb7bc36299da02d32400eb460f1e72855d) by [@farrokhi](https://github.com/farrokhi)).
- Add a more realistic and up to date dnseval output ([777c6f5](https://github.com/farrokhi/dnsdiag/commit/777c6f564e8fd3840a84fb946a792b8744363d59) by [@farrokhi](https://github.com/farrokhi)).
- Add json to dnseval tests ([162d7b1](https://github.com/farrokhi/dnsdiag/commit/162d7b1b0fa4be264c90711b843751c6e4fb60aa) by [@farrokhi](https://github.com/farrokhi)).
- Add EDNS flags display and improve output formatting in dnseval ([2316f77](https://github.com/farrokhi/dnsdiag/commit/2316f77557fec432764870a3227e94aead6cbca0) by [@farrokhi](https://github.com/farrokhi)).
- Add missing cli parameters in syntax help ([da46a1b](https://github.com/farrokhi/dnsdiag/commit/da46a1bf05305e7c852874502587215f01c586b0) by [@farrokhi](https://github.com/farrokhi)).
- Add DoQ and DoH3 protocol support to dnseval (#139) ([51e6fc8](https://github.com/farrokhi/dnsdiag/commit/51e6fc808404cf363138d81251815bfe6f600bee) by [@farrokhi](https://github.com/farrokhi)).
- Add type hints to shared DNS module and fix type syntax errors (#136) ([cda3402](https://github.com/farrokhi/dnsdiag/commit/cda34023b82897e28eb31f64fdda885c9fb542fb) by [@farrokhi](https://github.com/farrokhi)).
- Add tests ([1c9d163](https://github.com/farrokhi/dnsdiag/commit/1c9d16375942b1ca9bf9c171e7352edbbd030394) by [@farrokhi](https://github.com/farrokhi)).

### Fixed

- fix: default to AF_UNSPEC for automatic IPv4/IPv6 selection ([46f6235](https://github.com/farrokhi/dnsdiag/commit/46f623534394a9d9c8714e8252945b2b92bea0af) by [@farrokhi](https://github.com/farrokhi)).
- fix: correct DoH3 feature detection to check HTTPVersion.H3 ([7cfe3e9](https://github.com/farrokhi/dnsdiag/commit/7cfe3e940eadbb902e081a2a407e57e3237c1d52) by [@farrokhi](https://github.com/farrokhi)).
- Fix broken test when run from parent directory ([75903c6](https://github.com/farrokhi/dnsdiag/commit/75903c65def8b882e06be9f60cd9ddc580bf8a27) by [@farrokhi](https://github.com/farrokhi)).
- Fixed cookie display in dnsping ([455344d](https://github.com/farrokhi/dnsdiag/commit/455344ddf21e6b31a8f4ea8c1dbd311a8cd8a763) by [@farrokhi](https://github.com/farrokhi)).
- Fix: Only build packages when a new tag is pushed ([a2927e4](https://github.com/farrokhi/dnsdiag/commit/a2927e488dfde287e423aed625835fd027060241) by [@farrokhi](https://github.com/farrokhi)).
- Fix JSON Output Type Consistency ([af88b1b](https://github.com/farrokhi/dnsdiag/commit/af88b1b35d7c609c954c15a63567c9e9622806ad) by [@farrokhi](https://github.com/farrokhi)).
- Fix for IPv6 hostname resolution ([3f60d84](https://github.com/farrokhi/dnsdiag/commit/3f60d84cf42e44a645641091894434e22032c9af) by [@farrokhi](https://github.com/farrokhi)).
- Fix doh http version (#141) ([0ae5e93](https://github.com/farrokhi/dnsdiag/commit/0ae5e9388ffd028610a337d195cdbde32e1b7aa3) by [@farrokhi](https://github.com/farrokhi)).
- Fix formatting ([5801d7e](https://github.com/farrokhi/dnsdiag/commit/5801d7e1a09d812fb553a9dc8eb2070b60893dd3) by [@farrokhi](https://github.com/farrokhi)).

### Removed

- remove unnecessary files ([9e10740](https://github.com/farrokhi/dnsdiag/commit/9e10740c636f479f06a407f45c37c7a359c554c4) by [@farrokhi](https://github.com/farrokhi)).
- Remove stale email address ([99fd2fb](https://github.com/farrokhi/dnsdiag/commit/99fd2fbd0c137b5be26db06981121d86f6b4ab57) by [@farrokhi](https://github.com/farrokhi)).
- Remove unnecessary tests ([ff2b768](https://github.com/farrokhi/dnsdiag/commit/ff2b7685de66d29ea8c94ea411e4fa9d06e5caef) by [@farrokhi](https://github.com/farrokhi)).

## [v2.8.1](https://github.com/farrokhi/dnsdiag/releases/tag/v2.8.1) - 2025-10-04

<small>[Compare with v2.8.0](https://github.com/farrokhi/dnsdiag/compare/v2.8.0...v2.8.1)</small>

### Added

- Add support for DNS cookies through --cookie (Fixes #120) ([1bbe224](https://github.com/farrokhi/dnsdiag/commit/1bbe2240803ce4b696219ab744a1b592ef9c7010) by [@farrokhi](https://github.com/farrokhi)).

### Fixed

- Fix duplicate CLI parameter ([bdb88f6](https://github.com/farrokhi/dnsdiag/commit/bdb88f6c4e965530e62243b4cb08ac9e526737c1) by [@farrokhi](https://github.com/farrokhi)).
- Fix DoT/DoQ lookup when passing hostname instead of IP address ([dcc0bfd](https://github.com/farrokhi/dnsdiag/commit/dcc0bfd60fe927322777e6142899e463822b4947) by [@farrokhi](https://github.com/farrokhi)).
- Fix DNS hostname support for encrypted protocols (DoH/HTTP3) ([6dc0bf5](https://github.com/farrokhi/dnsdiag/commit/6dc0bf51676e30cd606962d6b0a6c68cafcb04ea) by [@farrokhi](https://github.com/farrokhi)).
- Fix displaying ECS payload - add missing request size ([2d788e7](https://github.com/farrokhi/dnsdiag/commit/2d788e72816770b442f9a865e39dc15635827b6a) by [@farrokhi](https://github.com/farrokhi)).

## [v2.8.0](https://github.com/farrokhi/dnsdiag/releases/tag/v2.8.0) - 2025-09-29

<small>[Compare with first commit](https://github.com/farrokhi/dnsdiag/compare/039fb2107d21f704860f6ebf96956d478b48a1fb...v2.8.0)</small>

### Added

- Add ECS examples to documentation ([8648262](https://github.com/farrokhi/dnsdiag/commit/8648262008d2ba682aaa7a9db4da4b2754d0c8ec) by [@farrokhi](https://github.com/farrokhi)).
- Add DoQ and DoH3 protocol support to dnstraceroute (#131) ([50dedb7](https://github.com/farrokhi/dnsdiag/commit/50dedb77b97e8593484525c43cd36567b7aa73ee) by [@farrokhi](https://github.com/farrokhi)).
- Add --ecs option (Fixes #110) (#128) ([aa50aa7](https://github.com/farrokhi/dnsdiag/commit/aa50aa738f41aac07204818b8fd747d7586bb0ca) by [@farrokhi](https://github.com/farrokhi)).
- Add `uv` examples ([d66d4bd](https://github.com/farrokhi/dnsdiag/commit/d66d4bdaf7f7556afb3241083e87643255d2d2af) by [@farrokhi](https://github.com/farrokhi)).
- Add help message that explains `--venv` parameter ([9fd73ec](https://github.com/farrokhi/dnsdiag/commit/9fd73ec501fa12d1c945ff072c7da72068699be1) by [@farrokhi](https://github.com/farrokhi)).
- Add missing -q to help message ([14dbce7](https://github.com/farrokhi/dnsdiag/commit/14dbce7bb575b64ea28c4af6faaae127a9347d0e) by [@farrokhi](https://github.com/farrokhi)).
- Add NextDNS and DNS4EU ([820b011](https://github.com/farrokhi/dnsdiag/commit/820b011d3a40609bad7fe32d51681458dc294329) by [@farrokhi](https://github.com/farrokhi)).
- Add support for DNS over QUIC (DoQ) protocol (#118) ([d14cfc3](https://github.com/farrokhi/dnsdiag/commit/d14cfc3bfedc25a22565c4ca1e84f8d3b2c26a9c) by [@farrokhi](https://github.com/farrokhi)).
- Add downloads/month badge ([cf8d53d](https://github.com/farrokhi/dnsdiag/commit/cf8d53d647cc6114b5669f716685fea20caf88f3) by [@farrokhi](https://github.com/farrokhi)).
- Add Wikimedia DNS resolver ([3623af3](https://github.com/farrokhi/dnsdiag/commit/3623af343663283eff9a5d23e028d6a970de5c5d) by [@farrokhi](https://github.com/farrokhi)).
- Add `-a` and `--answer` to display the first matching response (rdata) ([b321feb](https://github.com/farrokhi/dnsdiag/commit/b321feb7fcb1a2bd5f4f0d6620d73fa518c5fe5a) by [@farrokhi](https://github.com/farrokhi)).
- Add `-x` and `--expert` to display extra information ([7292af2](https://github.com/farrokhi/dnsdiag/commit/7292af27f17e406df069112b12d8535f68763f1f) by [@farrokhi](https://github.com/farrokhi)).
- Add `-T` and `--ttl` to display response TTL, if available ([a7f4ef1](https://github.com/farrokhi/dnsdiag/commit/a7f4ef1310e21f03eb0d146cd2180dc14b3681e0) by [@farrokhi](https://github.com/farrokhi)).
- Add support to override the default RR Class (fixes #114) ([f2fbc5d](https://github.com/farrokhi/dnsdiag/commit/f2fbc5d03570540d8ec13ce1ebfcb80b0e96ed33) by [@farrokhi](https://github.com/farrokhi)).
- Add new resolvers ([939ee86](https://github.com/farrokhi/dnsdiag/commit/939ee86e8eb9659973fad7ecd35e4c28324c3346) by [@farrokhi](https://github.com/farrokhi)).
- Add EDE support through `--ede` (Fixes #112) ([5609c58](https://github.com/farrokhi/dnsdiag/commit/5609c58d37fefb75d7443a9293661c849f2ecab7) by [@farrokhi](https://github.com/farrokhi)).
- Add --nsid to support RFC5001 NSID bit support ([c0c39f7](https://github.com/farrokhi/dnsdiag/commit/c0c39f7c33695ced2b4474efd01f538c960883f7) by [@farrokhi](https://github.com/farrokhi)).
- Add basic package builder logic ([2b5b3c7](https://github.com/farrokhi/dnsdiag/commit/2b5b3c7d405957b4e4a929a98ca62d940bdcd7e0) by [@farrokhi](https://github.com/farrokhi)).
- Add initial github actions config ([437ae45](https://github.com/farrokhi/dnsdiag/commit/437ae45a08fc128b42ad7d61a62286fc8a6c6f67) by [@farrokhi](https://github.com/farrokhi)).
- Add support for disabling recursion (-r) ([41cb7fa](https://github.com/farrokhi/dnsdiag/commit/41cb7fa403e45ece253fb8ec13c8e29d846bec9b) by [@farrokhi](https://github.com/farrokhi)).
- Add support for "-m" for cache-miss (Fixes #92) ([5cb3424](https://github.com/farrokhi/dnsdiag/commit/5cb34249944a1dd1ea6007d1f797ee00757d8232) by [@farrokhi](https://github.com/farrokhi)).
- Add support for sub-second intervals ([78a83fa](https://github.com/farrokhi/dnsdiag/commit/78a83fa3af2828598c9d70c603a6ec61f9bdab6b) by [@farrokhi](https://github.com/farrokhi)).
- Add PyPi counter badge ([5ee6422](https://github.com/farrokhi/dnsdiag/commit/5ee6422f95bffa787bd47ca0ed38be2b184e620b) by [@farrokhi](https://github.com/farrokhi)).
- Add cross platform package builder (#80) ([d677791](https://github.com/farrokhi/dnsdiag/commit/d6777917502c4c2674bb01cbfbb5c2863e57aa49) by [@farrokhi](https://github.com/farrokhi)).
- Add dnssec support to dnseval (#76) ([07c4a7d](https://github.com/farrokhi/dnsdiag/commit/07c4a7d324b9e08d2f20807be6c9d26b9a2c5121) by [@farrokhi](https://github.com/farrokhi)).
- Add Python 3.8 ([aede714](https://github.com/farrokhi/dnsdiag/commit/aede7146667591b73d4b02ca415454f1ad7981dd) by [@farrokhi](https://github.com/farrokhi)).
- Add docker badge ([aa58b5a](https://github.com/farrokhi/dnsdiag/commit/aa58b5a524847eb505d1f97923d911de96d8f920) by [@farrokhi](https://github.com/farrokhi)).
- Add Comodo and Verisign public DNS servers (#66) ([05485a9](https://github.com/farrokhi/dnsdiag/commit/05485a9db6aa413f68881fb1ddd436f10e79b662) by Brie Carranza).
- Add tox.ini ([9b0e1ac](https://github.com/farrokhi/dnsdiag/commit/9b0e1accbf896fead294c849a62b03f782949312) by [@farrokhi](https://github.com/farrokhi)).
- Add support for saving output to JSON ([1a7b467](https://github.com/farrokhi/dnsdiag/commit/1a7b467730f59ed92fed0e4c80f345614f12a80c) by Brie Carranza).
- Add -c0 support for infinite loop (fixes #57) ([3268fff](https://github.com/farrokhi/dnsdiag/commit/3268fffc0aedab1ec6f1518aa769455277d830f7) by [@farrokhi](https://github.com/farrokhi)).
- Add 3.8-dev target to test ([e54119c](https://github.com/farrokhi/dnsdiag/commit/e54119c7e8fc00631eba059ee4a04d6d8567e3c7) by [@farrokhi](https://github.com/farrokhi)).
- Add build-matrix support ([a4e250e](https://github.com/farrokhi/dnsdiag/commit/a4e250ec187035046b9fc87cff7dd769baf24434) by [@farrokhi](https://github.com/farrokhi)).
- Add license scan report and status ([1beb5ee](https://github.com/farrokhi/dnsdiag/commit/1beb5ee513dc2ec31ce0ca6ec6f532c5a248c113) by fossabot).
- Add sample input file with IPv4 address of public resolvers ([35a116d](https://github.com/farrokhi/dnsdiag/commit/35a116d65ec000b9071357e4d62077ef5b873a7d) by [@farrokhi](https://github.com/farrokhi)).
- Add CloudFlare's new resolver (v4/v6) (Fixes #51) ([f0a9cfb](https://github.com/farrokhi/dnsdiag/commit/f0a9cfb7d81f1e3a4f6bb47a6b2c805816345952) by [@farrokhi](https://github.com/farrokhi)).
- Add `-m` to force cache-miss measurement in dnseval (Closes #41) ([2a05c54](https://github.com/farrokhi/dnsdiag/commit/2a05c547eb607acdabc5c8da5f17a1959af4b8df) by [@farrokhi](https://github.com/farrokhi)).
- Add color mode to dnseval ("-C" option) ([ea07cee](https://github.com/farrokhi/dnsdiag/commit/ea07cee12a17cc8a188f7580704b37920503d2ec) by [@farrokhi](https://github.com/farrokhi)).
- Add verbose mode to print actual response(s) (FIX #28) ([79e0e86](https://github.com/farrokhi/dnsdiag/commit/79e0e86046c2b5c3c6c1ad0c5c6e6fe0c00716bb) by [@farrokhi](https://github.com/farrokhi)).
- Add option to pause between each dnsping request ([4c4e890](https://github.com/farrokhi/dnsdiag/commit/4c4e8909d08316bf7e5d8c9b3646673ceeaff253) by Hamish Coleman).
- Add EDNS0 support and update docs ([e7b21cf](https://github.com/farrokhi/dnsdiag/commit/e7b21cf0874754072873caf441ac56e93bc79616) by [@farrokhi](https://github.com/farrokhi)).
- Add support for EDNS0 flag ([118f84e](https://github.com/farrokhi/dnsdiag/commit/118f84ee6609ff2db6e3e537ae48abe23752b940) by [@farrokhi](https://github.com/farrokhi)).
- Add list of root servers as example for dnseval ([b1e45e7](https://github.com/farrokhi/dnsdiag/commit/b1e45e728bd2671fa5af2556b153228d0e61ac79) by [@farrokhi](https://github.com/farrokhi)).
- Add --tcp/-T option (fix #19) ([660954f](https://github.com/farrokhi/dnsdiag/commit/660954f8268b2e3f8109fcc0428862f8a30e9930) by [@farrokhi](https://github.com/farrokhi)).
- Add original dnspython as submodule ([efc1455](https://github.com/farrokhi/dnsdiag/commit/efc14554920a34bb7d57b14a1c7fe620f7279ffa) by [@farrokhi](https://github.com/farrokhi)).
- Add relevant category ([44e0389](https://github.com/farrokhi/dnsdiag/commit/44e0389cd61ca1993b702a716815accf81f3fe39) by [@farrokhi](https://github.com/farrokhi)).
- Add requirements.txt, now we depend on dnspython ([3157250](https://github.com/farrokhi/dnsdiag/commit/31572502878ef5e315a3526ad378da030e2debe9) by [@farrokhi](https://github.com/farrokhi)).
- add initial dnsdiag.py tool - the DNS diagnostics swiss army knife ([4d19e4a](https://github.com/farrokhi/dnsdiag/commit/4d19e4aadce3b8811f349c0175622a1f3dced026) by [@farrokhi](https://github.com/farrokhi)).
- add flags in dnseval output and update docs (close #13) ([9ae9c59](https://github.com/farrokhi/dnsdiag/commit/9ae9c594a80532dfefdd9efbd9cc895dcd26516d) by [@farrokhi](https://github.com/farrokhi)).
- add -4 and -6 to enforce network layer protocol (closes #9) ([423c59d](https://github.com/farrokhi/dnsdiag/commit/423c59d5c408e0c0cb0900d4581dd2f2ec385265) by [@farrokhi](https://github.com/farrokhi)).
- add possibility of using TCP instead of UDP ([c9b9e71](https://github.com/farrokhi/dnsdiag/commit/c9b9e71723a77d9196843a803db8695f7daf31ad) by [@farrokhi](https://github.com/farrokhi)).
- add basic unit test for nose ([17849ed](https://github.com/farrokhi/dnsdiag/commit/17849edb669650c2554eb1e396c858482a1425b5) by [@farrokhi](https://github.com/farrokhi)).
- add some badges of honor! ([e52b85d](https://github.com/farrokhi/dnsdiag/commit/e52b85d2c6f607aaf5b25a0a19ef6f8e08867fea) by [@farrokhi](https://github.com/farrokhi)).
- add expert hint and colorful mode ([9da2ccf](https://github.com/farrokhi/dnsdiag/commit/9da2ccf7ebfe98aed8e28fd492d587445220a55a) by [@farrokhi](https://github.com/farrokhi)).
- add installation instructions ([c6acf0d](https://github.com/farrokhi/dnsdiag/commit/c6acf0d1c57c911354127507a68e08e7efc4dc57) by [@farrokhi](https://github.com/farrokhi)).
- add link to github ([507fb62](https://github.com/farrokhi/dnsdiag/commit/507fb625adcc88f675f9dcd82fa9843b6a9c6167) by [@farrokhi](https://github.com/farrokhi)).
- add build status from travis ([2929637](https://github.com/farrokhi/dnsdiag/commit/2929637bc05ba84a478540d1f2142268dd1a9787) by [@farrokhi](https://github.com/farrokhi)).
- add travis-ci support ([b7f7772](https://github.com/farrokhi/dnsdiag/commit/b7f777221b415dde73dce3af73ab88da64798fa6) by [@farrokhi](https://github.com/farrokhi)).
- add setuptools support ([f82879b](https://github.com/farrokhi/dnsdiag/commit/f82879bf70dd7d6f9569cf32a9e2af88efe60029) by [@farrokhi](https://github.com/farrokhi)).
- add ability to define arbitrary src port and IP address ([6505d5f](https://github.com/farrokhi/dnsdiag/commit/6505d5fe1a9ebbc665cffb048bd441ea9508f272) by [@farrokhi](https://github.com/farrokhi)).
- add "-n" option to disable reverse lookups ([5d405b4](https://github.com/farrokhi/dnsdiag/commit/5d405b45eb8e612048550686b6fe85a0126e08fc) by [@farrokhi](https://github.com/farrokhi)).
- add option to use arbitrary DNS port number (default 53) ([b25735d](https://github.com/farrokhi/dnsdiag/commit/b25735d7e7e475279898620299422189df18051b) by [@farrokhi](https://github.com/farrokhi)).
- add Credits section ([539278d](https://github.com/farrokhi/dnsdiag/commit/539278d55d9d01a1400b761f380bbc737da44ef2) by [@farrokhi](https://github.com/farrokhi)).
- add support for AS Number and name in trace (fix #7) ([9752234](https://github.com/farrokhi/dnsdiag/commit/97522347b70b989885f206bfc52db6f0b0695aab) by [@farrokhi](https://github.com/farrokhi)).
- add initial version of dnstraceroute utility ([8bd7977](https://github.com/farrokhi/dnsdiag/commit/8bd79771dd18227013ac1f416f9b0ae95404ee1e) by [@farrokhi](https://github.com/farrokhi)).
- add opendns to sample file ([f84053d](https://github.com/farrokhi/dnsdiag/commit/f84053d73f74bf8690792e4a41cea93a6aee90de) by [@farrokhi](https://github.com/farrokhi)).
- add dnsperf.list sample file ([f3b8745](https://github.com/farrokhi/dnsdiag/commit/f3b8745e23fba56d5ef6aa5c92c7d7225a05c47f) by [@farrokhi](https://github.com/farrokhi)).
- add examples ([8195004](https://github.com/farrokhi/dnsdiag/commit/81950042bf8bd27fdc9004450da265dff8a804f2) by [@farrokhi](https://github.com/farrokhi)).

### Fixed

- Fix inconsistent help message ([ee25d18](https://github.com/farrokhi/dnsdiag/commit/ee25d18bb9cb1e275d203657651cbb9fc27f1003) by [@farrokhi](https://github.com/farrokhi)).
- Fix inconsistent command line parameters ([12698a8](https://github.com/farrokhi/dnsdiag/commit/12698a85b98e4c1629400e3d00a63bcb074b1516) by [@farrokhi](https://github.com/farrokhi)).
- Fix inconsistent CLI parameters ([17371d4](https://github.com/farrokhi/dnsdiag/commit/17371d4b8f8d13ad7cbc06079858dda0b2fe5cd4) by [@farrokhi](https://github.com/farrokhi)).
- Fix alignment ([08d379f](https://github.com/farrokhi/dnsdiag/commit/08d379fd3a5eb59f8fec0fe1ef6af620e5a631f0) by [@farrokhi](https://github.com/farrokhi)).
- Fix RTT display (broken in a recent commit) ([6bf8fc2](https://github.com/farrokhi/dnsdiag/commit/6bf8fc2a80fa72f6988ae8758ab8f2a3eb24bae8) by [@farrokhi](https://github.com/farrokhi)).
- Fix missing `-p` parameter (Fixes #106) ([099552f](https://github.com/farrokhi/dnsdiag/commit/099552f55b2fa52bda9355bd1a95ddf22b46c961) by [@farrokhi](https://github.com/farrokhi)).
- Fix version extraction during build ([55b29bf](https://github.com/farrokhi/dnsdiag/commit/55b29bf2e381f1436c981b68bb1498728eeefc66) by [@farrokhi](https://github.com/farrokhi)).
- fix: disable orange in non-colored mode" (#93) ([c1dbde2](https://github.com/farrokhi/dnsdiag/commit/c1dbde2c4ea3cb1ae5331ae7da0ee7c4cda90e45) by xhdix).
- Fix incorrect double-dash flag to enable "cache-miss" for dnseval (#91) ([3f8f629](https://github.com/farrokhi/dnsdiag/commit/3f8f629ec5aa95b4b797d05bc282e784ebd7b929) by Oscar Busk).
- Fix dependency version ([57bc745](https://github.com/farrokhi/dnsdiag/commit/57bc745dd7cc9c27b0d8174bf052a03c15ecc9ac) by [@farrokhi](https://github.com/farrokhi)).
- Fix docker badge ([c1807e3](https://github.com/farrokhi/dnsdiag/commit/c1807e3b10031e0e5b81b7f28ed8d7664789c49d) by [@farrokhi](https://github.com/farrokhi)).
- Fix link to article ([2d3069d](https://github.com/farrokhi/dnsdiag/commit/2d3069d80a2f63651817660b5d33b54054a1e5f5) by [@farrokhi](https://github.com/farrokhi)).
- Fix statistics calculation (Fix #64) ([7af735b](https://github.com/farrokhi/dnsdiag/commit/7af735b22be68f1d54094084f930f78eb0c3957e) by Babak Farrokhi).
- Fix travis config to build 3.7 and 3.8-dev ([814da79](https://github.com/farrokhi/dnsdiag/commit/814da79cb2c85df4a26fed72d200311a9f377912) by [@farrokhi](https://github.com/farrokhi)).
- Fixing 3.7 build again ([3f1325f](https://github.com/farrokhi/dnsdiag/commit/3f1325fafd3bdfec4fbe6459cf186256c9a2d6e1) by [@farrokhi](https://github.com/farrokhi)).
- Fix badges ([3037784](https://github.com/farrokhi/dnsdiag/commit/303778475e3a30b3e0d6215208ceb75dd4a8d059) by [@farrokhi](https://github.com/farrokhi)).
- Fix sample input filename in README ([8b9bf4f](https://github.com/farrokhi/dnsdiag/commit/8b9bf4feeb55205fabda440b3654ac300a1c2b86) by [@farrokhi](https://github.com/farrokhi)).
- Fix setuptools ([86d4a19](https://github.com/farrokhi/dnsdiag/commit/86d4a1932ff6844be7bf2b5a14302e7f241f43ae) by [@farrokhi](https://github.com/farrokhi)).
- Fix setuptool installation and dependecies ([51641d7](https://github.com/farrokhi/dnsdiag/commit/51641d7367b2460fe31da544c76eaeb8b7b69782) by [@farrokhi](https://github.com/farrokhi)).
- Fix display in case of no answer (fix #34) ([dd2899c](https://github.com/farrokhi/dnsdiag/commit/dd2899c3497cb3876bd225009edf61568b0ae314) by [@farrokhi](https://github.com/farrokhi)).
- Fix string formatting ([233898a](https://github.com/farrokhi/dnsdiag/commit/233898a4a25af2af0059f4d6c04a9a9dadc1aa8f) by [@farrokhi](https://github.com/farrokhi)).
- Fix build with Travis CI ([6704180](https://github.com/farrokhi/dnsdiag/commit/6704180df5e7424a9c84f17245040b8228a00202) by [@farrokhi](https://github.com/farrokhi)).
- Fix handling invalid TTL and some output string justifications (fix #26, #27) ([cf3cfcc](https://github.com/farrokhi/dnsdiag/commit/cf3cfcc49395a4a560e099b39dacf7c08295f1c9) by [@farrokhi](https://github.com/farrokhi)).
- Fix conflicting -e switch (--expert and --edns). ([e0bed3c](https://github.com/farrokhi/dnsdiag/commit/e0bed3c07f97bc6298eaa624c2521d299b204e63) by [@farrokhi](https://github.com/farrokhi)).
- Fix looking up NS record from root server ([6779dc0](https://github.com/farrokhi/dnsdiag/commit/6779dc0b9d7972b3ff3814f058ec6ba95dde631d) by [@farrokhi](https://github.com/farrokhi)).
- Fix bug in dealing with root servers ([fe78505](https://github.com/farrokhi/dnsdiag/commit/fe785056373b3b2a8c0add450f2e4da6897e0887) by [@farrokhi](https://github.com/farrokhi)).
- Fix text alignment ([b779440](https://github.com/farrokhi/dnsdiag/commit/b779440a1ede2d6d8436ef3dea5aa6ca1ade2d6f) by [@farrokhi](https://github.com/farrokhi)).
- fix long arguments ([627e53f](https://github.com/farrokhi/dnsdiag/commit/627e53f1a858ee1fd700eb0be52e9a804e076972) by [@farrokhi](https://github.com/farrokhi)).
- fix README and code cleanup ([4dd5065](https://github.com/farrokhi/dnsdiag/commit/4dd5065c73b954f4f51378b22fd77cde947bcfde) by [@farrokhi](https://github.com/farrokhi)).
- fix NoAnswer error when RRSIG requested (fix #14) ([1cc5a38](https://github.com/farrokhi/dnsdiag/commit/1cc5a38a4b4f05a9eebc5ac046bba8825039478d) by [@farrokhi](https://github.com/farrokhi)).
- fix script names for setuptools ([846d980](https://github.com/farrokhi/dnsdiag/commit/846d980a09dc70da2a6193e53f0e8ae47dd81aa3) by [@farrokhi](https://github.com/farrokhi)).
- fix crash when resolving dns hostname to IP (close #9) ([848ea0f](https://github.com/farrokhi/dnsdiag/commit/848ea0f34cf33c44d8d5802e3f81b5d9ff33e8de) by [@farrokhi](https://github.com/farrokhi)).
- fix variable name after recent refactoring ([0b512b5](https://github.com/farrokhi/dnsdiag/commit/0b512b537a0065996f065c65f1874d312053d37b) by [@farrokhi](https://github.com/farrokhi)).
- fix stddev calculaction logic ([c754115](https://github.com/farrokhi/dnsdiag/commit/c7541154c050cb28034ce215dac500e12dcaae02) by [@farrokhi](https://github.com/farrokhi)).
- fix a calculation bug with "-c1" (closes #10) ([ca49f66](https://github.com/farrokhi/dnsdiag/commit/ca49f667809e1f32b82594b19f5a9cfca34417c1) by [@farrokhi](https://github.com/farrokhi)).
- fix typo ([3ea3434](https://github.com/farrokhi/dnsdiag/commit/3ea343467d593016f1f409f7e37656e7160067a0) by [@farrokhi](https://github.com/farrokhi)).
- fix markdown spacing ([1ce9d41](https://github.com/farrokhi/dnsdiag/commit/1ce9d41672c99bf08de8e1ed3dd2e0eef378d0dd) by [@farrokhi](https://github.com/farrokhi)).
- fix cymruwhois dependency for setuptools ([986871a](https://github.com/farrokhi/dnsdiag/commit/986871a5b918d7a69a9853ede55e0254de6119f0) by [@farrokhi](https://github.com/farrokhi)).
- fixed dependecy mismatch ([8a5b84a](https://github.com/farrokhi/dnsdiag/commit/8a5b84adb084194e1c0143bacecba97ab7a985da) by [@farrokhi](https://github.com/farrokhi)).
- fix signal issue in Windows ([026d127](https://github.com/farrokhi/dnsdiag/commit/026d12730d0f87dd8fe320681fd8a030e033bf3a) by [@farrokhi](https://github.com/farrokhi)).
- fix signal handling error on windows ([8b40cea](https://github.com/farrokhi/dnsdiag/commit/8b40cea4a9fa66870c609130ffeec0d0935d5be3) by [@farrokhi](https://github.com/farrokhi)).
- fix links ([d8ce420](https://github.com/farrokhi/dnsdiag/commit/d8ce420686557c663894746436a5a1751d416265) by [@farrokhi](https://github.com/farrokhi)).
- fix layout with variable len addresses (close #4) ([d18925b](https://github.com/farrokhi/dnsdiag/commit/d18925b1e3baf852ef0959d2acef45dfb6d480d9) by [@farrokhi](https://github.com/farrokhi)).
- fixed line-wrapping in text files ([e104136](https://github.com/farrokhi/dnsdiag/commit/e104136c15ba7de8d5bf6def2fa4f69d354ebab9) by [@farrokhi](https://github.com/farrokhi)).
- fix syntax ([6ea6f7e](https://github.com/farrokhi/dnsdiag/commit/6ea6f7e0cf4d40f1fddd6953f69e881fd997b10b) by [@farrokhi](https://github.com/farrokhi)).
- fix arbitrary dns server assignment bug ([251703c](https://github.com/farrokhi/dnsdiag/commit/251703c0be0af345f648201c4060536be26e2b49) by [@farrokhi](https://github.com/farrokhi)).

### Changed

- Change EDNS buffer size to 1232 to avoid fragmentation (Fixes #111) ([424f828](https://github.com/farrokhi/dnsdiag/commit/424f828a7f5996e868dfba138321ed846388789a) by [@farrokhi](https://github.com/farrokhi)).
- Change default behavior of --edns to disabled by default (Fixes #97) (#99) ([4d6512d](https://github.com/farrokhi/dnsdiag/commit/4d6512d0d4b91da111ee09fffeeea3fac33a0f42) by [@farrokhi](https://github.com/farrokhi)).
- Change default ping interval to 1 second ([a1f9c65](https://github.com/farrokhi/dnsdiag/commit/a1f9c65bbee439c9309f4339c744ece436d319d7) by [@farrokhi](https://github.com/farrokhi)).
- Change default timeout value to 2 (was 5) (fix #24) ([89c0db0](https://github.com/farrokhi/dnsdiag/commit/89c0db04a603ba61982143887ccdb0910d0e6a57) by [@farrokhi](https://github.com/farrokhi)).
- Change separator line ([6ed1068](https://github.com/farrokhi/dnsdiag/commit/6ed1068241730a9c634e5a23fe683637c000d2f4) by [@farrokhi](https://github.com/farrokhi)).

### Removed

- Remove pypy from build ([a6abfbb](https://github.com/farrokhi/dnsdiag/commit/a6abfbbe3be211ff87d216b31d125f0c44c5b00f) by [@farrokhi](https://github.com/farrokhi)).
- Remove funding file ([71bc51a](https://github.com/farrokhi/dnsdiag/commit/71bc51ae75047edcbedd7de24e092ddc0ebcd0cf) by [@farrokhi](https://github.com/farrokhi)).
- Remove artifact ([1825ce6](https://github.com/farrokhi/dnsdiag/commit/1825ce6519628d248d7ce14f02002e907c590f93) by [@farrokhi](https://github.com/farrokhi)).
- Remove unneeded badges ([b532394](https://github.com/farrokhi/dnsdiag/commit/b5323940b7a34b4b4216ee248b5a2902ccba39af) by [@farrokhi](https://github.com/farrokhi)).
- Remove older python ([53b9ce1](https://github.com/farrokhi/dnsdiag/commit/53b9ce1cd98d366d318899a22391e632cc49a433) by [@farrokhi](https://github.com/farrokhi)).
- Remove a leftover debug message ([0d65361](https://github.com/farrokhi/dnsdiag/commit/0d65361f46415a70781e0f898aa8cf1996ad42c2) by [@farrokhi](https://github.com/farrokhi)).
- Remove local dnspython submodule since the latest dnspython (as of 1.15.0) supports all the requirements ([f1c3e76](https://github.com/farrokhi/dnsdiag/commit/f1c3e76b8c042c7c0702b9bf76e331bf0fd8d618) by [@farrokhi](https://github.com/farrokhi)).
- Remove -e from examples ([ebf09d3](https://github.com/farrokhi/dnsdiag/commit/ebf09d3800f40edcf4ea7e34ea00afa20b2a98ec) by [@farrokhi](https://github.com/farrokhi)).
- Remove dnspython from external requirements ([e9f4625](https://github.com/farrokhi/dnsdiag/commit/e9f4625b86cb6e1b90228bae1e51fa702ea61a48) by [@farrokhi](https://github.com/farrokhi)).
- remove patched dnspython module and use stock version ([1a10ae0](https://github.com/farrokhi/dnsdiag/commit/1a10ae0ce986d959a43cd5ae91d05210543c174c) by [@farrokhi](https://github.com/farrokhi)).
- Remove AF ([f84388b](https://github.com/farrokhi/dnsdiag/commit/f84388be939b1dd57ca90672f22809f35dddc764) by [@farrokhi](https://github.com/farrokhi)).
- remove unnecessary option ([d568b3b](https://github.com/farrokhi/dnsdiag/commit/d568b3b57c99b85e0cc90f99ce6660f73e55ffe4) by [@farrokhi](https://github.com/farrokhi)).

## [v2.9.3](https://github.com/farrokhi/dnsdiag/releases/tag/v2.9.3) - 2026-01-31

<small>[Compare with v2.9.2](https://github.com/farrokhi/dnsdiag/compare/v2.9.2...v2.9.3)</small>

### Fixed

- fix: remove Windows ARM64 from CI build matrix ([04f8b62](https://github.com/farrokhi/dnsdiag/commit/04f8b62)) by [@farrokhi](https://github.com/farrokhi)). Removed Windows ARM64 platform from build workflow and documentation due to cryptography dependency lacking pre-built wheels for this platform.
- fix: replace unreliable dnspython timing with perf_counter measurements ([0a3a5f6](https://github.com/farrokhi/dnsdiag/commit/0a3a5f6)) by [@farrokhi](https://github.com/farrokhi)). Improves response time accuracy across all DNS protocols.
- fix: improved error handling for DoH, DoH3 and DoQ ([6d14c1f](https://github.com/farrokhi/dnsdiag/commit/6d14c1f)) by [@farrokhi](https://github.com/farrokhi)). Better user-friendly error messages instead of Python stack traces for modern DNS protocols.
- fix: treat connection refused as transient across all DNS protocols ([099d627](https://github.com/farrokhi/dnsdiag/commit/099d627)) by [@farrokhi](https://github.com/farrokhi)). DoH, DoH3, and DoQ now continue pinging when connection is refused (like UDP/TCP), showing error messages and collecting packet loss statistics uniformly across all protocols.
- fix: handle transient QUIC connection failures gracefully ([87b2285](https://github.com/farrokhi/dnsdiag/commit/87b2285)) by [@farrokhi](https://github.com/farrokhi)). Treats UnexpectedEOF exceptions as transient failures that should be retried.
- fix: correctly detect Windows ARM64 architecture in build script ([6d36c8b](https://github.com/farrokhi/dnsdiag/commit/6d36c8b)) by [@farrokhi](https://github.com/farrokhi)). Uses MSYSTEM_CARCH environment variable on Windows.

## [2.9.1](https://github.com/farrokhi/dnsdiag/releases/tag/2.9.1) - 2025-10-31

<small>[Compare with v2.9.0](https://github.com/farrokhi/dnsdiag/compare/v2.9.0...2.9.1)</small>

### Fixed

- fix: truncate cookie display in normal mode to 8 characters ([6d8f609](https://github.com/farrokhi/dnsdiag/commit/6d8f6098cdf666bd2cbf6ad5805bafdabec99cb3) by [@farrokhi](https://github.com/farrokhi)).
- fix: include root-level Python modules in package distribution ([0470053](https://github.com/farrokhi/dnsdiag/commit/047005321125a5393eebdb0f24e792e07e85cde3) by [@farrokhi](https://github.com/farrokhi)).

## [v2.9.0](https://github.com/farrokhi/dnsdiag/releases/tag/v2.9.0) - 2025-10-26

<small>[Compare with v2.8.1](https://github.com/farrokhi/dnsdiag/compare/v2.8.1...v2.9.0)</small>

### Added

- Add --nsid support to dnstraceroute (#153) ([85d96f6](https://github.com/farrokhi/dnsdiag/commit/85d96f66d2cfa36d5fd47d2fb5022f269e23aecb) by [@farrokhi](https://github.com/farrokhi)).
- Add tests for cookie feature in dnsping ([66b4faa](https://github.com/farrokhi/dnsdiag/commit/66b4faa80fbf8b2cbe94e8f73e942400715a40ef) by [@farrokhi](https://github.com/farrokhi)).
- Add support for Python 3.14 ([8099260](https://github.com/farrokhi/dnsdiag/commit/8099260c69d159844c2790bdd0064e943c847e03) by [@farrokhi](https://github.com/farrokhi)).
- Add marker to disable IPv6 tests on Github Action ([a756d10](https://github.com/farrokhi/dnsdiag/commit/a756d10bc22b57ad00273200528b1955c73271f0) by [@farrokhi](https://github.com/farrokhi)).
- Add Windows to test suite ([1e1cbdb](https://github.com/farrokhi/dnsdiag/commit/1e1cbdb5f745a67bddaabf9cc83da5b755115f7b) by [@farrokhi](https://github.com/farrokhi)).
- Add GitHub Actions workflow for running pytest integration tests ([4f4021c](https://github.com/farrokhi/dnsdiag/commit/4f4021c0fd51ce36017dee0884ec44cdc3981e08) by [@farrokhi](https://github.com/farrokhi)).
- Add type checking to tests ([93324be](https://github.com/farrokhi/dnsdiag/commit/93324beb7bc36299da02d32400eb460f1e72855d) by [@farrokhi](https://github.com/farrokhi)).
- Add a more realistic and up to date dnseval output ([777c6f5](https://github.com/farrokhi/dnsdiag/commit/777c6f564e8fd3840a84fb946a792b8744363d59) by [@farrokhi](https://github.com/farrokhi)).
- Add json to dnseval tests ([162d7b1](https://github.com/farrokhi/dnsdiag/commit/162d7b1b0fa4be264c90711b843751c6e4fb60aa) by [@farrokhi](https://github.com/farrokhi)).
- Add EDNS flags display and improve output formatting in dnseval ([2316f77](https://github.com/farrokhi/dnsdiag/commit/2316f77557fec432764870a3227e94aead6cbca0) by [@farrokhi](https://github.com/farrokhi)).
- Add missing cli parameters in syntax help ([da46a1b](https://github.com/farrokhi/dnsdiag/commit/da46a1bf05305e7c852874502587215f01c586b0) by [@farrokhi](https://github.com/farrokhi)).
- Add DoQ and DoH3 protocol support to dnseval (#139) ([51e6fc8](https://github.com/farrokhi/dnsdiag/commit/51e6fc808404cf363138d81251815bfe6f600bee) by [@farrokhi](https://github.com/farrokhi)).
- Add type hints to shared DNS module and fix type syntax errors (#136) ([cda3402](https://github.com/farrokhi/dnsdiag/commit/cda34023b82897e28eb31f64fdda885c9fb542fb) by [@farrokhi](https://github.com/farrokhi)).
- Add tests ([1c9d163](https://github.com/farrokhi/dnsdiag/commit/1c9d16375942b1ca9bf9c171e7352edbbd030394) by [@farrokhi](https://github.com/farrokhi)).

### Fixed

- fix: default to AF_UNSPEC for automatic IPv4/IPv6 selection ([46f6235](https://github.com/farrokhi/dnsdiag/commit/46f623534394a9d9c8714e8252945b2b92bea0af) by [@farrokhi](https://github.com/farrokhi)).
- fix: correct DoH3 feature detection to check HTTPVersion.H3 ([7cfe3e9](https://github.com/farrokhi/dnsdiag/commit/7cfe3e940eadbb902e081a2a407e57e3237c1d52) by [@farrokhi](https://github.com/farrokhi)).
- Fix broken test when run from parent directory ([75903c6](https://github.com/farrokhi/dnsdiag/commit/75903c65def8b882e06be9f60cd9ddc580bf8a27) by [@farrokhi](https://github.com/farrokhi)).
- Fixed cookie display in dnsping ([455344d](https://github.com/farrokhi/dnsdiag/commit/455344ddf21e6b31a8f4ea8c1dbd311a8cd8a763) by [@farrokhi](https://github.com/farrokhi)).
- Fix: Only build packages when a new tag is pushed ([a2927e4](https://github.com/farrokhi/dnsdiag/commit/a2927e488dfde287e423aed625835fd027060241) by [@farrokhi](https://github.com/farrokhi)).
- Fix JSON Output Type Consistency ([af88b1b](https://github.com/farrokhi/dnsdiag/commit/af88b1b35d7c609c954c15a63567c9e9622806ad) by [@farrokhi](https://github.com/farrokhi)).
- Fix for IPv6 hostname resolution ([3f60d84](https://github.com/farrokhi/dnsdiag/commit/3f60d84cf42e44a645641091894434e22032c9af) by [@farrokhi](https://github.com/farrokhi)).
- Fix doh http version (#141) ([0ae5e93](https://github.com/farrokhi/dnsdiag/commit/0ae5e9388ffd028610a337d195cdbde32e1b7aa3) by [@farrokhi](https://github.com/farrokhi)).
- Fix formatting ([5801d7e](https://github.com/farrokhi/dnsdiag/commit/5801d7e1a09d812fb553a9dc8eb2070b60893dd3) by [@farrokhi](https://github.com/farrokhi)).

### Removed

- remove unnecessary files ([9e10740](https://github.com/farrokhi/dnsdiag/commit/9e10740c636f479f06a407f45c37c7a359c554c4) by [@farrokhi](https://github.com/farrokhi)).
- Remove stale email address ([99fd2fb](https://github.com/farrokhi/dnsdiag/commit/99fd2fbd0c137b5be26db06981121d86f6b4ab57) by [@farrokhi](https://github.com/farrokhi)).
- Remove unnecessary tests ([ff2b768](https://github.com/farrokhi/dnsdiag/commit/ff2b7685de66d29ea8c94ea411e4fa9d06e5caef) by [@farrokhi](https://github.com/farrokhi)).




## [v2.8.1](https://github.com/farrokhi/dnsdiag/releases/tag/v2.8.1) - 2025-10-04

<small>[Compare with v2.8.0](https://github.com/farrokhi/dnsdiag/compare/v2.8.0...v2.8.1)</small>

### Added

- Add support for DNS cookies through --cookie (Fixes #120) ([1bbe224](https://github.com/farrokhi/dnsdiag/commit/1bbe2240803ce4b696219ab744a1b592ef9c7010) by [@farrokhi](https://github.com/farrokhi)).

### Fixed

- Fix duplicate CLI parameter ([bdb88f6](https://github.com/farrokhi/dnsdiag/commit/bdb88f6c4e965530e62243b4cb08ac9e526737c1) by [@farrokhi](https://github.com/farrokhi)).
- Fix DoT/DoQ lookup when passing hostname instead of IP address ([dcc0bfd](https://github.com/farrokhi/dnsdiag/commit/dcc0bfd60fe927322777e6142899e463822b4947) by [@farrokhi](https://github.com/farrokhi)).
- Fix DNS hostname support for encrypted protocols (DoH/HTTP3) ([6dc0bf5](https://github.com/farrokhi/dnsdiag/commit/6dc0bf51676e30cd606962d6b0a6c68cafcb04ea) by [@farrokhi](https://github.com/farrokhi)).
- Fix displaying ECS payload - add missing request size ([2d788e7](https://github.com/farrokhi/dnsdiag/commit/2d788e72816770b442f9a865e39dc15635827b6a) by [@farrokhi](https://github.com/farrokhi)).

## [v2.8.0](https://github.com/farrokhi/dnsdiag/releases/tag/v2.8.0) - 2025-09-29

<small>[Compare with first commit](https://github.com/farrokhi/dnsdiag/compare/039fb2107d21f704860f6ebf96956d478b48a1fb...v2.8.0)</small>

### Added

- Add ECS examples to documentation ([8648262](https://github.com/farrokhi/dnsdiag/commit/8648262008d2ba682aaa7a9db4da4b2754d0c8ec) by [@farrokhi](https://github.com/farrokhi)).
- Add DoQ and DoH3 protocol support to dnstraceroute (#131) ([50dedb7](https://github.com/farrokhi/dnsdiag/commit/50dedb77b97e8593484525c43cd36567b7aa73ee) by [@farrokhi](https://github.com/farrokhi)).
- Add --ecs option (Fixes #110) (#128) ([aa50aa7](https://github.com/farrokhi/dnsdiag/commit/aa50aa738f41aac07204818b8fd747d7586bb0ca) by [@farrokhi](https://github.com/farrokhi)).
- Add `uv` examples ([d66d4bd](https://github.com/farrokhi/dnsdiag/commit/d66d4bdaf7f7556afb3241083e87643255d2d2af) by [@farrokhi](https://github.com/farrokhi)).
- Add help message that explains `--venv` parameter ([9fd73ec](https://github.com/farrokhi/dnsdiag/commit/9fd73ec501fa12d1c945ff072c7da72068699be1) by [@farrokhi](https://github.com/farrokhi)).
- Add missing -q to help message ([14dbce7](https://github.com/farrokhi/dnsdiag/commit/14dbce7bb575b64ea28c4af6faaae127a9347d0e) by [@farrokhi](https://github.com/farrokhi)).
- Add NextDNS and DNS4EU ([820b011](https://github.com/farrokhi/dnsdiag/commit/820b011d3a40609bad7fe32d51681458dc294329) by [@farrokhi](https://github.com/farrokhi)).
- Add support for DNS over QUIC (DoQ) protocol (#118) ([d14cfc3](https://github.com/farrokhi/dnsdiag/commit/d14cfc3bfedc25a22565c4ca1e84f8d3b2c26a9c) by [@farrokhi](https://github.com/farrokhi)).
- Add downloads/month badge ([cf8d53d](https://github.com/farrokhi/dnsdiag/commit/cf8d53d647cc6114b5669f716685fea20caf88f3) by [@farrokhi](https://github.com/farrokhi)).
- Add Wikimedia DNS resolver ([3623af3](https://github.com/farrokhi/dnsdiag/commit/3623af343663283eff9a5d23e028d6a970de5c5d) by [@farrokhi](https://github.com/farrokhi)).
- Add `-a` and `--answer` to display the first matching response (rdata) ([b321feb](https://github.com/farrokhi/dnsdiag/commit/b321feb7fcb1a2bd5f4f0d6620d73fa518c5fe5a) by [@farrokhi](https://github.com/farrokhi)).
- Add `-x` and `--expert` to display extra information ([7292af2](https://github.com/farrokhi/dnsdiag/commit/7292af27f17e406df069112b12d8535f68763f1f) by [@farrokhi](https://github.com/farrokhi)).
- Add `-T` and `--ttl` to display response TTL, if available ([a7f4ef1](https://github.com/farrokhi/dnsdiag/commit/a7f4ef1310e21f03eb0d146cd2180dc14b3681e0) by [@farrokhi](https://github.com/farrokhi)).
- Add support to override the default RR Class (fixes #114) ([f2fbc5d](https://github.com/farrokhi/dnsdiag/commit/f2fbc5d03570540d8ec13ce1ebfcb80b0e96ed33) by [@farrokhi](https://github.com/farrokhi)).
- Add new resolvers ([939ee86](https://github.com/farrokhi/dnsdiag/commit/939ee86e8eb9659973fad7ecd35e4c28324c3346) by [@farrokhi](https://github.com/farrokhi)).
- Add EDE support through `--ede` (Fixes #112) ([5609c58](https://github.com/farrokhi/dnsdiag/commit/5609c58d37fefb75d7443a9293661c849f2ecab7) by [@farrokhi](https://github.com/farrokhi)).
- Add --nsid to support RFC5001 NSID bit support ([c0c39f7](https://github.com/farrokhi/dnsdiag/commit/c0c39f7c33695ced2b4474efd01f538c960883f7) by [@farrokhi](https://github.com/farrokhi)).
- Add basic package builder logic ([2b5b3c7](https://github.com/farrokhi/dnsdiag/commit/2b5b3c7d405957b4e4a929a98ca62d940bdcd7e0) by [@farrokhi](https://github.com/farrokhi)).
- Add initial github actions config ([437ae45](https://github.com/farrokhi/dnsdiag/commit/437ae45a08fc128b42ad7d61a62286fc8a6c6f67) by [@farrokhi](https://github.com/farrokhi)).
- Add support for disabling recursion (-r) ([41cb7fa](https://github.com/farrokhi/dnsdiag/commit/41cb7fa403e45ece253fb8ec13c8e29d846bec9b) by [@farrokhi](https://github.com/farrokhi)).
- Add support for "-m" for cache-miss (Fixes #92) ([5cb3424](https://github.com/farrokhi/dnsdiag/commit/5cb34249944a1dd1ea6007d1f797ee00757d8232) by [@farrokhi](https://github.com/farrokhi)).
- Add support for sub-second intervals ([78a83fa](https://github.com/farrokhi/dnsdiag/commit/78a83fa3af2828598c9d70c603a6ec61f9bdab6b) by [@farrokhi](https://github.com/farrokhi)).
- Add PyPi counter badge ([5ee6422](https://github.com/farrokhi/dnsdiag/commit/5ee6422f95bffa787bd47ca0ed38be2b184e620b) by [@farrokhi](https://github.com/farrokhi)).
- Add cross platform package builder (#80) ([d677791](https://github.com/farrokhi/dnsdiag/commit/d6777917502c4c2674bb01cbfbb5c2863e57aa49) by [@farrokhi](https://github.com/farrokhi)).
- Add dnssec support to dnseval (#76) ([07c4a7d](https://github.com/farrokhi/dnsdiag/commit/07c4a7d324b9e08d2f20807be6c9d26b9a2c5121) by [@farrokhi](https://github.com/farrokhi)).
- Add Python 3.8 ([aede714](https://github.com/farrokhi/dnsdiag/commit/aede7146667591b73d4b02ca415454f1ad7981dd) by [@farrokhi](https://github.com/farrokhi)).
- Add docker badge ([aa58b5a](https://github.com/farrokhi/dnsdiag/commit/aa58b5a524847eb505d1f97923d911de96d8f920) by [@farrokhi](https://github.com/farrokhi)).
- Add Comodo and Verisign public DNS servers (#66) ([05485a9](https://github.com/farrokhi/dnsdiag/commit/05485a9db6aa413f68881fb1ddd436f10e79b662) by Brie Carranza).
- Add tox.ini ([9b0e1ac](https://github.com/farrokhi/dnsdiag/commit/9b0e1accbf896fead294c849a62b03f782949312) by [@farrokhi](https://github.com/farrokhi)).
- Add support for saving output to JSON ([1a7b467](https://github.com/farrokhi/dnsdiag/commit/1a7b467730f59ed92fed0e4c80f345614f12a80c) by Brie Carranza).
- Add -c0 support for infinite loop (fixes #57) ([3268fff](https://github.com/farrokhi/dnsdiag/commit/3268fffc0aedab1ec6f1518aa769455277d830f7) by [@farrokhi](https://github.com/farrokhi)).
- Add 3.8-dev target to test ([e54119c](https://github.com/farrokhi/dnsdiag/commit/e54119c7e8fc00631eba059ee4a04d6d8567e3c7) by [@farrokhi](https://github.com/farrokhi)).
- Add build-matrix support ([a4e250e](https://github.com/farrokhi/dnsdiag/commit/a4e250ec187035046b9fc87cff7dd769baf24434) by [@farrokhi](https://github.com/farrokhi)).
- Add license scan report and status ([1beb5ee](https://github.com/farrokhi/dnsdiag/commit/1beb5ee513dc2ec31ce0ca6ec6f532c5a248c113) by fossabot).
- Add sample input file with IPv4 address of public resolvers ([35a116d](https://github.com/farrokhi/dnsdiag/commit/35a116d65ec000b9071357e4d62077ef5b873a7d) by [@farrokhi](https://github.com/farrokhi)).
- Add CloudFlare's new resolver (v4/v6) (Fixes #51) ([f0a9cfb](https://github.com/farrokhi/dnsdiag/commit/f0a9cfb7d81f1e3a4f6bb47a6b2c805816345952) by [@farrokhi](https://github.com/farrokhi)).
- Add `-m` to force cache-miss measurement in dnseval (Closes #41) ([2a05c54](https://github.com/farrokhi/dnsdiag/commit/2a05c547eb607acdabc5c8da5f17a1959af4b8df) by [@farrokhi](https://github.com/farrokhi)).
- Add color mode to dnseval ("-C" option) ([ea07cee](https://github.com/farrokhi/dnsdiag/commit/ea07cee12a17cc8a188f7580704b37920503d2ec) by [@farrokhi](https://github.com/farrokhi)).
- Add verbose mode to print actual response(s) (FIX #28) ([79e0e86](https://github.com/farrokhi/dnsdiag/commit/79e0e86046c2b5c3c6c1ad0c5c6e6fe0c00716bb) by [@farrokhi](https://github.com/farrokhi)).
- Add option to pause between each dnsping request ([4c4e890](https://github.com/farrokhi/dnsdiag/commit/4c4e8909d08316bf7e5d8c9b3646673ceeaff253) by Hamish Coleman).
- Add EDNS0 support and update docs ([e7b21cf](https://github.com/farrokhi/dnsdiag/commit/e7b21cf0874754072873caf441ac56e93bc79616) by [@farrokhi](https://github.com/farrokhi)).
- Add support for EDNS0 flag ([118f84e](https://github.com/farrokhi/dnsdiag/commit/118f84ee6609ff2db6e3e537ae48abe23752b940) by [@farrokhi](https://github.com/farrokhi)).
- Add list of root servers as example for dnseval ([b1e45e7](https://github.com/farrokhi/dnsdiag/commit/b1e45e728bd2671fa5af2556b153228d0e61ac79) by [@farrokhi](https://github.com/farrokhi)).
- Add --tcp/-T option (fix #19) ([660954f](https://github.com/farrokhi/dnsdiag/commit/660954f8268b2e3f8109fcc0428862f8a30e9930) by [@farrokhi](https://github.com/farrokhi)).
- Add original dnspython as submodule ([efc1455](https://github.com/farrokhi/dnsdiag/commit/efc14554920a34bb7d57b14a1c7fe620f7279ffa) by [@farrokhi](https://github.com/farrokhi)).
- Add relevant category ([44e0389](https://github.com/farrokhi/dnsdiag/commit/44e0389cd61ca1993b702a716815accf81f3fe39) by [@farrokhi](https://github.com/farrokhi)).
- Add requirements.txt, now we depend on dnspython ([3157250](https://github.com/farrokhi/dnsdiag/commit/31572502878ef5e315a3526ad378da030e2debe9) by [@farrokhi](https://github.com/farrokhi)).
- add initial dnsdiag.py tool - the DNS diagnostics swiss army knife ([4d19e4a](https://github.com/farrokhi/dnsdiag/commit/4d19e4aadce3b8811f349c0175622a1f3dced026) by [@farrokhi](https://github.com/farrokhi)).
- add flags in dnseval output and update docs (close #13) ([9ae9c59](https://github.com/farrokhi/dnsdiag/commit/9ae9c594a80532dfefdd9efbd9cc895dcd26516d) by [@farrokhi](https://github.com/farrokhi)).
- add -4 and -6 to enforce network layer protocol (closes #9) ([423c59d](https://github.com/farrokhi/dnsdiag/commit/423c59d5c408e0c0cb0900d4581dd2f2ec385265) by [@farrokhi](https://github.com/farrokhi)).
- add possibility of using TCP instead of UDP ([c9b9e71](https://github.com/farrokhi/dnsdiag/commit/c9b9e71723a77d9196843a803db8695f7daf31ad) by [@farrokhi](https://github.com/farrokhi)).
- add basic unit test for nose ([17849ed](https://github.com/farrokhi/dnsdiag/commit/17849edb669650c2554eb1e396c858482a1425b5) by [@farrokhi](https://github.com/farrokhi)).
- add some badges of honor! ([e52b85d](https://github.com/farrokhi/dnsdiag/commit/e52b85d2c6f607aaf5b25a0a19ef6f8e08867fea) by [@farrokhi](https://github.com/farrokhi)).
- add expert hint and colorful mode ([9da2ccf](https://github.com/farrokhi/dnsdiag/commit/9da2ccf7ebfe98aed8e28fd492d587445220a55a) by [@farrokhi](https://github.com/farrokhi)).
- add installation instructions ([c6acf0d](https://github.com/farrokhi/dnsdiag/commit/c6acf0d1c57c911354127507a68e08e7efc4dc57) by [@farrokhi](https://github.com/farrokhi)).
- add link to github ([507fb62](https://github.com/farrokhi/dnsdiag/commit/507fb625adcc88f675f9dcd82fa9843b6a9c6167) by [@farrokhi](https://github.com/farrokhi)).
- add build status from travis ([2929637](https://github.com/farrokhi/dnsdiag/commit/2929637bc05ba84a478540d1f2142268dd1a9787) by [@farrokhi](https://github.com/farrokhi)).
- add travis-ci support ([b7f7772](https://github.com/farrokhi/dnsdiag/commit/b7f777221b415dde73dce3af73ab88da64798fa6) by [@farrokhi](https://github.com/farrokhi)).
- add setuptools support ([f82879b](https://github.com/farrokhi/dnsdiag/commit/f82879bf70dd7d6f9569cf32a9e2af88efe60029) by [@farrokhi](https://github.com/farrokhi)).
- add ability to define arbitrary src port and IP address ([6505d5f](https://github.com/farrokhi/dnsdiag/commit/6505d5fe1a9ebbc665cffb048bd441ea9508f272) by [@farrokhi](https://github.com/farrokhi)).
- add "-n" option to disable reverse lookups ([5d405b4](https://github.com/farrokhi/dnsdiag/commit/5d405b45eb8e612048550686b6fe85a0126e08fc) by [@farrokhi](https://github.com/farrokhi)).
- add option to use arbitrary DNS port number (default 53) ([b25735d](https://github.com/farrokhi/dnsdiag/commit/b25735d7e7e475279898620299422189df18051b) by [@farrokhi](https://github.com/farrokhi)).
- add Credits section ([539278d](https://github.com/farrokhi/dnsdiag/commit/539278d55d9d01a1400b761f380bbc737da44ef2) by [@farrokhi](https://github.com/farrokhi)).
- add support for AS Number and name in trace (fix #7) ([9752234](https://github.com/farrokhi/dnsdiag/commit/97522347b70b989885f206bfc52db6f0b0695aab) by [@farrokhi](https://github.com/farrokhi)).
- add initial version of dnstraceroute utility ([8bd7977](https://github.com/farrokhi/dnsdiag/commit/8bd79771dd18227013ac1f416f9b0ae95404ee1e) by [@farrokhi](https://github.com/farrokhi)).
- add opendns to sample file ([f84053d](https://github.com/farrokhi/dnsdiag/commit/f84053d73f74bf8690792e4a41cea93a6aee90de) by [@farrokhi](https://github.com/farrokhi)).
- add dnsperf.list sample file ([f3b8745](https://github.com/farrokhi/dnsdiag/commit/f3b8745e23fba56d5ef6aa5c92c7d7225a05c47f) by [@farrokhi](https://github.com/farrokhi)).
- add examples ([8195004](https://github.com/farrokhi/dnsdiag/commit/81950042bf8bd27fdc9004450da265dff8a804f2) by [@farrokhi](https://github.com/farrokhi)).

### Fixed

- Fix inconsistent help message ([ee25d18](https://github.com/farrokhi/dnsdiag/commit/ee25d18bb9cb1e275d203657651cbb9fc27f1003) by [@farrokhi](https://github.com/farrokhi)).
- Fix inconsistent command line parameters ([12698a8](https://github.com/farrokhi/dnsdiag/commit/12698a85b98e4c1629400e3d00a63bcb074b1516) by [@farrokhi](https://github.com/farrokhi)).
- Fix inconsistent CLI parameters ([17371d4](https://github.com/farrokhi/dnsdiag/commit/17371d4b8f8d13ad7cbc06079858dda0b2fe5cd4) by [@farrokhi](https://github.com/farrokhi)).
- Fix alignment ([08d379f](https://github.com/farrokhi/dnsdiag/commit/08d379fd3a5eb59f8fec0fe1ef6af620e5a631f0) by [@farrokhi](https://github.com/farrokhi)).
- Fix RTT display (broken in a recent commit) ([6bf8fc2](https://github.com/farrokhi/dnsdiag/commit/6bf8fc2a80fa72f6988ae8758ab8f2a3eb24bae8) by [@farrokhi](https://github.com/farrokhi)).
- Fix missing `-p` parameter (Fixes #106) ([099552f](https://github.com/farrokhi/dnsdiag/commit/099552f55b2fa52bda9355bd1a95ddf22b46c961) by [@farrokhi](https://github.com/farrokhi)).
- Fix version extraction during build ([55b29bf](https://github.com/farrokhi/dnsdiag/commit/55b29bf2e381f1436c981b68bb1498728eeefc66) by [@farrokhi](https://github.com/farrokhi)).
- fix: disable orange in non-colored mode" (#93) ([c1dbde2](https://github.com/farrokhi/dnsdiag/commit/c1dbde2c4ea3cb1ae5331ae7da0ee7c4cda90e45) by xhdix).
- Fix incorrect double-dash flag to enable "cache-miss" for dnseval (#91) ([3f8f629](https://github.com/farrokhi/dnsdiag/commit/3f8f629ec5aa95b4b797d05bc282e784ebd7b929) by Oscar Busk).
- Fix dependency version ([57bc745](https://github.com/farrokhi/dnsdiag/commit/57bc745dd7cc9c27b0d8174bf052a03c15ecc9ac) by [@farrokhi](https://github.com/farrokhi)).
- Fix docker badge ([c1807e3](https://github.com/farrokhi/dnsdiag/commit/c1807e3b10031e0e5b81b7f28ed8d7664789c49d) by [@farrokhi](https://github.com/farrokhi)).
- Fix link to article ([2d3069d](https://github.com/farrokhi/dnsdiag/commit/2d3069d80a2f63651817660b5d33b54054a1e5f5) by [@farrokhi](https://github.com/farrokhi)).
- Fix statistics calculation (Fix #64) ([7af735b](https://github.com/farrokhi/dnsdiag/commit/7af735b22be68f1d54094084f930f78eb0c3957e) by [@farrokhi](https://github.com/farrokhi)).
- Fix travis config to build 3.7 and 3.8-dev ([814da79](https://github.com/farrokhi/dnsdiag/commit/814da79cb2c85df4a26fed72d200311a9f377912) by [@farrokhi](https://github.com/farrokhi)).
- Fixing 3.7 build again ([3f1325f](https://github.com/farrokhi/dnsdiag/commit/3f1325fafd3bdfec4fbe6459cf186256c9a2d6e1) by [@farrokhi](https://github.com/farrokhi)).
- Fix badges ([3037784](https://github.com/farrokhi/dnsdiag/commit/303778475e3a30b3e0d6215208ceb75dd4a8d059) by [@farrokhi](https://github.com/farrokhi)).
- Fix sample input filename in README ([8b9bf4f](https://github.com/farrokhi/dnsdiag/commit/8b9bf4feeb55205fabda440b3654ac300a1c2b86) by [@farrokhi](https://github.com/farrokhi)).
- Fix setuptools ([86d4a19](https://github.com/farrokhi/dnsdiag/commit/86d4a1932ff6844be7bf2b5a14302e7f241f43ae) by [@farrokhi](https://github.com/farrokhi)).
- Fix setuptool installation and dependecies ([51641d7](https://github.com/farrokhi/dnsdiag/commit/51641d7367b2460fe31da544c76eaeb8b7b69782) by [@farrokhi](https://github.com/farrokhi)).
- Fix display in case of no answer (fix #34) ([dd2899c](https://github.com/farrokhi/dnsdiag/commit/dd2899c3497cb3876bd225009edf61568b0ae314) by [@farrokhi](https://github.com/farrokhi)).
- Fix string formatting ([233898a](https://github.com/farrokhi/dnsdiag/commit/233898a4a25af2af0059f4d6c04a9a9dadc1aa8f) by [@farrokhi](https://github.com/farrokhi)).
- Fix build with Travis CI ([6704180](https://github.com/farrokhi/dnsdiag/commit/6704180df5e7424a9c84f17245040b8228a00202) by [@farrokhi](https://github.com/farrokhi)).
- Fix handling invalid TTL and some output string justifications (fix #26, #27) ([cf3cfcc](https://github.com/farrokhi/dnsdiag/commit/cf3cfcc49395a4a560e099b39dacf7c08295f1c9) by [@farrokhi](https://github.com/farrokhi)).
- Fix conflicting -e switch (--expert and --edns). ([e0bed3c](https://github.com/farrokhi/dnsdiag/commit/e0bed3c07f97bc6298eaa624c2521d299b204e63) by [@farrokhi](https://github.com/farrokhi)).
- Fix looking up NS record from root server ([6779dc0](https://github.com/farrokhi/dnsdiag/commit/6779dc0b9d7972b3ff3814f058ec6ba95dde631d) by [@farrokhi](https://github.com/farrokhi)).
- Fix bug in dealing with root servers ([fe78505](https://github.com/farrokhi/dnsdiag/commit/fe785056373b3b2a8c0add450f2e4da6897e0887) by [@farrokhi](https://github.com/farrokhi)).
- Fix text alignment ([b779440](https://github.com/farrokhi/dnsdiag/commit/b779440a1ede2d6d8436ef3dea5aa6ca1ade2d6f) by [@farrokhi](https://github.com/farrokhi)).
- fix long arguments ([627e53f](https://github.com/farrokhi/dnsdiag/commit/627e53f1a858ee1fd700eb0be52e9a804e076972) by [@farrokhi](https://github.com/farrokhi)).
- fix README and code cleanup ([4dd5065](https://github.com/farrokhi/dnsdiag/commit/4dd5065c73b954f4f51378b22fd77cde947bcfde) by [@farrokhi](https://github.com/farrokhi)).
- fix NoAnswer error when RRSIG requested (fix #14) ([1cc5a38](https://github.com/farrokhi/dnsdiag/commit/1cc5a38a4b4f05a9eebc5ac046bba8825039478d) by [@farrokhi](https://github.com/farrokhi)).
- fix script names for setuptools ([846d980](https://github.com/farrokhi/dnsdiag/commit/846d980a09dc70da2a6193e53f0e8ae47dd81aa3) by [@farrokhi](https://github.com/farrokhi)).
- fix crash when resolving dns hostname to IP (close #9) ([848ea0f](https://github.com/farrokhi/dnsdiag/commit/848ea0f34cf33c44d8d5802e3f81b5d9ff33e8de) by [@farrokhi](https://github.com/farrokhi)).
- fix variable name after recent refactoring ([0b512b5](https://github.com/farrokhi/dnsdiag/commit/0b512b537a0065996f065c65f1874d312053d37b) by [@farrokhi](https://github.com/farrokhi)).
- fix stddev calculaction logic ([c754115](https://github.com/farrokhi/dnsdiag/commit/c7541154c050cb28034ce215dac500e12dcaae02) by [@farrokhi](https://github.com/farrokhi)).
- fix a calculation bug with "-c1" (closes #10) ([ca49f66](https://github.com/farrokhi/dnsdiag/commit/ca49f667809e1f32b82594b19f5a9cfca34417c1) by [@farrokhi](https://github.com/farrokhi)).
- fix typo ([3ea3434](https://github.com/farrokhi/dnsdiag/commit/3ea343467d593016f1f409f7e37656e7160067a0) by [@farrokhi](https://github.com/farrokhi)).
- fix markdown spacing ([1ce9d41](https://github.com/farrokhi/dnsdiag/commit/1ce9d41672c99bf08de8e1ed3dd2e0eef378d0dd) by [@farrokhi](https://github.com/farrokhi)).
- fix cymruwhois dependency for setuptools ([986871a](https://github.com/farrokhi/dnsdiag/commit/986871a5b918d7a69a9853ede55e0254de6119f0) by [@farrokhi](https://github.com/farrokhi)).
- fixed dependecy mismatch ([8a5b84a](https://github.com/farrokhi/dnsdiag/commit/8a5b84adb084194e1c0143bacecba97ab7a985da) by [@farrokhi](https://github.com/farrokhi)).
- fix signal issue in Windows ([026d127](https://github.com/farrokhi/dnsdiag/commit/026d12730d0f87dd8fe320681fd8a030e033bf3a) by [@farrokhi](https://github.com/farrokhi)).
- fix signal handling error on windows ([8b40cea](https://github.com/farrokhi/dnsdiag/commit/8b40cea4a9fa66870c609130ffeec0d0935d5be3) by [@farrokhi](https://github.com/farrokhi)).
- fix links ([d8ce420](https://github.com/farrokhi/dnsdiag/commit/d8ce420686557c663894746436a5a1751d416265) by [@farrokhi](https://github.com/farrokhi)).
- fix layout with variable len addresses (close #4) ([d18925b](https://github.com/farrokhi/dnsdiag/commit/d18925b1e3baf852ef0959d2acef45dfb6d480d9) by [@farrokhi](https://github.com/farrokhi)).
- fixed line-wrapping in text files ([e104136](https://github.com/farrokhi/dnsdiag/commit/e104136c15ba7de8d5bf6def2fa4f69d354ebab9) by [@farrokhi](https://github.com/farrokhi)).
- fix syntax ([6ea6f7e](https://github.com/farrokhi/dnsdiag/commit/6ea6f7e0cf4d40f1fddd6953f69e881fd997b10b) by [@farrokhi](https://github.com/farrokhi)).
- fix arbitrary dns server assignment bug ([251703c](https://github.com/farrokhi/dnsdiag/commit/251703c0be0af345f648201c4060536be26e2b49) by [@farrokhi](https://github.com/farrokhi)).

### Changed

- Change EDNS buffer size to 1232 to avoid fragmentation (Fixes #111) ([424f828](https://github.com/farrokhi/dnsdiag/commit/424f828a7f5996e868dfba138321ed846388789a) by [@farrokhi](https://github.com/farrokhi)).
- Change default behavior of --edns to disabled by default (Fixes #97) (#99) ([4d6512d](https://github.com/farrokhi/dnsdiag/commit/4d6512d0d4b91da111ee09fffeeea3fac33a0f42) by [@farrokhi](https://github.com/farrokhi)).
- Change default ping interval to 1 second ([a1f9c65](https://github.com/farrokhi/dnsdiag/commit/a1f9c65bbee439c9309f4339c744ece436d319d7) by [@farrokhi](https://github.com/farrokhi)).
- Change default timeout value to 2 (was 5) (fix #24) ([89c0db0](https://github.com/farrokhi/dnsdiag/commit/89c0db04a603ba61982143887ccdb0910d0e6a57) by [@farrokhi](https://github.com/farrokhi)).
- Change separator line ([6ed1068](https://github.com/farrokhi/dnsdiag/commit/6ed1068241730a9c634e5a23fe683637c000d2f4) by [@farrokhi](https://github.com/farrokhi)).

### Removed

- Remove pypy from build ([a6abfbb](https://github.com/farrokhi/dnsdiag/commit/a6abfbbe3be211ff87d216b31d125f0c44c5b00f) by [@farrokhi](https://github.com/farrokhi)).
- Remove funding file ([71bc51a](https://github.com/farrokhi/dnsdiag/commit/71bc51ae75047edcbedd7de24e092ddc0ebcd0cf) by [@farrokhi](https://github.com/farrokhi)).
- Remove artifact ([1825ce6](https://github.com/farrokhi/dnsdiag/commit/1825ce6519628d248d7ce14f02002e907c590f93) by [@farrokhi](https://github.com/farrokhi)).
- Remove unneeded badges ([b532394](https://github.com/farrokhi/dnsdiag/commit/b5323940b7a34b4b4216ee248b5a2902ccba39af) by [@farrokhi](https://github.com/farrokhi)).
- Remove older python ([53b9ce1](https://github.com/farrokhi/dnsdiag/commit/53b9ce1cd98d366d318899a22391e632cc49a433) by [@farrokhi](https://github.com/farrokhi)).
- Remove a leftover debug message ([0d65361](https://github.com/farrokhi/dnsdiag/commit/0d65361f46415a70781e0f898aa8cf1996ad42c2) by [@farrokhi](https://github.com/farrokhi)).
- Remove local dnspython submodule since the latest dnspython (as of 1.15.0) supports all the requirements ([f1c3e76](https://github.com/farrokhi/dnsdiag/commit/f1c3e76b8c042c7c0702b9bf76e331bf0fd8d618) by [@farrokhi](https://github.com/farrokhi)).
- Remove -e from examples ([ebf09d3](https://github.com/farrokhi/dnsdiag/commit/ebf09d3800f40edcf4ea7e34ea00afa20b2a98ec) by [@farrokhi](https://github.com/farrokhi)).
- Remove dnspython from external requirements ([e9f4625](https://github.com/farrokhi/dnsdiag/commit/e9f4625b86cb6e1b90228bae1e51fa702ea61a48) by [@farrokhi](https://github.com/farrokhi)).
- remove patched dnspython module and use stock version ([1a10ae0](https://github.com/farrokhi/dnsdiag/commit/1a10ae0ce986d959a43cd5ae91d05210543c174c) by [@farrokhi](https://github.com/farrokhi)).
- Remove AF ([f84388b](https://github.com/farrokhi/dnsdiag/commit/f84388be939b1dd57ca90672f22809f35dddc764) by [@farrokhi](https://github.com/farrokhi)).
- remove unnecessary option ([d568b3b](https://github.com/farrokhi/dnsdiag/commit/d568b3b57c99b85e0cc90f99ce6660f73e55ffe4) by [@farrokhi](https://github.com/farrokhi)).
