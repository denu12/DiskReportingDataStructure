FROM archlinux:base-devel-20261004.0.606936@sha256:996c3a1d6b0d87b01242f6fcd8cfa3ad3eece1a67ab5c8f108e20af1d7b97bdd
# The dated image fixes the base. Arch packages are rolling; retain pacman-Q output.
RUN pacman -Syu --noconfirm --needed git python python-pip rustup clang cmake ninja pkgconf openssl curl wget unzip zip bazelisk && pacman -Scc --noconfirm
RUN useradd -m -u 1000 benchmark
WORKDIR /opt/disk-range-report
COPY --chown=benchmark:benchmark . .
RUN mkdir -p data results bin build && chown -R benchmark:benchmark data results bin build
USER benchmark
ENV PATH="/home/benchmark/.cargo/bin:/opt/disk-range-report/.venv/bin:${PATH}" DRR_BACKEND=process
RUN bash tools/setup_arch.sh && BAZEL=bazelisk bash tools/build_arch.sh && pacman -Q > results/build/arch-packages.txt
ENTRYPOINT ["python", "run_theater.py"]
CMD ["--help"]
