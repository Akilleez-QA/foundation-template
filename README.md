<p align="center"><img src=".github/assets/social-preview.png" alt="foundation-template" width="100%"></p>

# foundation-template

A minimal working Foundation to copy when you start a new domain

<img src="https://img.shields.io/badge/license-GPL--3.0--only-2400FF?style=flat-square&labelColor=000000"> <img src="https://img.shields.io/badge/python-3.11%2B-6E61FF?style=flat-square&labelColor=000000">

## Status

Version 0.1.0. 1 read-only tool(s) behind a stdio JSON-RPC bridge, standard library only. Every result carries Evidence and an input hash. A verdict is an observation, not an acceptance decision.

## Quickstart

```
git clone https://github.com/Akilleez-QA/foundation-template
cd foundation-template
python -B -m unittest discover -s tests -t .
python -B tools/build_manifest.py
```

## What is inside

| Tool | Purpose |
|---|---|
| `echo_observation` | PLACEHOLDER: returns its validated input as an observation with Evidence |

## Measured

4 tests pass with `python -B -m unittest discover -s tests -t .` on Python 3.14.8 (normal and `-O`), at the initial commit. CI: local only.

## Documentation

See [docs/README.md](docs/README.md): requirements, architecture, interface control, verification matrix, configuration management, and the [domain guide](docs/guides/explanation/domain-guide.md).

## Related projects

foundation-template is one of the Foundations. A Foundation owns one domain's meaning, data and acceptance. [POODO](https://github.com/Akilleez-QA/poodo) governs how Foundations are used, and Cstack hosts them: it starts each Foundation's bridge, pins its source manifest and checks every result (see [the ICD](docs/icd/icd-cstack.md)).

| Project | Tie |
|---|---|
| Cstack | Host. Runs this Foundation through a pinned stdio adapter |
| [poodo](https://github.com/Akilleez-QA/poodo) | Governs how Foundations are used |
| [foundation-engine](https://github.com/Akilleez-QA/foundation-engine) | Sibling Foundation |
| [foundation-math](https://github.com/Akilleez-QA/foundation-math) | Sibling Foundation |
| [foundation-film](https://github.com/Akilleez-QA/foundation-film) | Sibling Foundation |
| [foundation-refrigeration](https://github.com/Akilleez-QA/foundation-refrigeration) | Sibling Foundation |
| [foundation-robotics](https://github.com/Akilleez-QA/foundation-robotics) | Sibling Foundation |
| [endoforge](https://github.com/Akilleez-QA/endoforge) | Producers that measure; Foundations judge their outputs |

## Layout

| Path | Contents |
|---|---|
| `foundation_template/` | Domain package |
| `foundation_template_bridge/` | stdio JSON-RPC bridge and schemas |
| `tests/` | Unit and bridge tests |
| `tools/` | Manifest and data tools |
| `docs/` | Requirements, architecture, ICD, verification, configuration, guides |
| `SOURCE-MANIFEST.json` | SHA-256 of every shipped file |

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) and [SECURITY.md](SECURITY.md).

## License

This project is available under the GNU General Public License v3.0 only (GPL-3.0-only). If you want to use it to create a product or service under different terms, commercial licenses are available from Refrigeration.AI. Contact craig@nh3.biz.
