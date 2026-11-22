"""Prepare the requested frozen executables and a higher-dimensional SPRK driver."""

import json
import os
from pathlib import Path
import subprocess

ROOT=Path(__file__).resolve().parent
PROJECT=ROOT.parents[1]
WORK=PROJECT/"results/_queue-coverage-completion-20261030/workspace"


def main():
    source=WORK/"src/runner/dimensional/rust/sprk_ids_main.rs"
    driver=(WORK/"src/runner/dimensional/rust/driver.rs").read_text()
    driver=driver.replace('let kind=if IDS_ONLY {"esa_sprk"} else {kind};',
                          'let kind=if IDS_ONLY {"esa_sprk"} else {kind};')
    dims=set()
    for campaign in ("ESA_clustering","ESA_graph_embeddings","ESA_high_dimensional","ESA_uniform_points"):
        manifest=json.loads((PROJECT/"results/_queue-indexicon-20261105/workspace/data"/campaign/"campaign.json").read_text())
        dims.update(row.get("dimension",0) for row in manifest["cases"])
    dims.discard(0)
    # Exact coordinate reporting follows the existing Rust dimensional driver.
    text=source.read_text().replace('const IDS_ONLY:bool=true;', 'const IDS_ONLY:bool=false;')
    text=text.replace('assert_eq!(kind,"esa_sprk","Unknown original SPRK backend");',
                      'assert_eq!(kind,"esa_sprk_RUST_EXACT_DDIM","Unknown SPRK backend");')
    text=text.replace('include!("driver.rs");','include!("driver.rs");')
    for relative in ("dvec.rs","query.rs"):
        text=text.replace('../../../third_party/esa2026/src/'+relative,
                          str(WORK/"src/third_party/esa2026/src"/relative))
    start=driver.index(' match d{')
    driver=driver[:start]+' match d{'+''.join(f'{d}=>run::<{d}>(&mut f,&args[2]),' for d in sorted(dims))+'_=>panic!("Unsupported dimension")}\n}\n'
    stage=ROOT/"sprk-driver"
    stage.mkdir(exist_ok=True)
    (stage/"main.rs").write_text(text)
    (stage/"driver.rs").write_text(driver)
    sprk=WORK/"src/third_party/esa2026/sprk"
    (stage/"Cargo.toml").write_text(
        '[package]\nname="requested-sprk-ddim"\nversion="0.1.0"\nedition="2024"\n'
        '[workspace]\n[[bin]]\nname="sprk-ddim"\npath="main.rs"\n'
        '[dependencies]\nsprk={path='+json.dumps(str(sprk))+'}\n')
    env=dict(os.environ,CARGO_HOME=str(PROJECT.parent/"SFC-Index/toolchains/cargo"),
             RUSTUP_HOME=str(PROJECT.parent/"SFC-Index/toolchains/rustup"),
             RUSTUP_TOOLCHAIN="stable",RUSTFLAGS="-C target-cpu=native",CARGO_BUILD_JOBS="1")
    env["PATH"]=env["CARGO_HOME"]+"/bin:"+env["PATH"]
    subprocess.run(["cargo","build","--offline","--release","--manifest-path",str(stage/"Cargo.toml")],env=env,check=True)


if __name__=="__main__":
    main()
