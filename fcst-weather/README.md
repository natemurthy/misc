# fcst-weather

Small sandbox for experimenting with transformer-based weather forecasting models with solar irradiance support.

> [!NOTE]
> GPU profiling shows Aurora inference costs roughly 5–10x more compute and memory than AIFS ENS 2.0.

Just a reminder that the Aurora model, which has 1.3 billion parameters, is 5.7x larger than the AIFS ENS 2.0 model at
229 million. So in terms of GPU utiliziation:

1. The Aurora model is larger
2. Aurora's 3D Swin backbone attends over the full 0.25° lat/lon volume (721×1440 ≈ 1.04M grid columns × 13 pressure
   levels), whereas AIFS's graph encoder immediately compresses its N320 grid (~542k points — already half as many)
   down to a much smaller latent mesh, and its heavy transformer processor runs only on that reduced mesh;
3. The hourly example performs 24 forward > passes for a 24 h horizon (4 backbone steps × 6 hourly fine lead times) and
   offloads each full-grid prediction to host memory, while the AIFS example performs 4 passes and extracts a single
   grid point per step.


## Microsoft Aurora

Files: `example_msft_aurora_solar{_test}.py`

Aurora 1.5 uses a 3D Swin Transformer backbone with Perceiver encoders/decoders.

So far this has been easier to work with in terms of dependency management; however, it has this strange random weights
initiatlization step I don't fully understand. The model is also a bit larger compared the AINS ENS model.

Aurora 1.5 produces hourly output natively: its variable lead-time embeddings let each 6-hour backbone step be
sub-stepped hourly (`fine_lead_times=[1..6]`), so `example_msft_aurora_solar.py` logs 24 hourly-mean SSRD values.
AIFS ENS cannot do this — see "Hourly granularity and temporal disaggregation" below.



## ECMWF's AIFS ENS

Files: `example_ecmwf_*.py`

AIFS ENS relies on graph neural network (GNN) encoders/decoders paired with a sliding-window transformer processor.

The dependency management toolchain for this code has been a bit trickier. On Python 3.14, I have to be very carefully
about pinning the version of each module needed at import. For instance, there's no pre-built wheel for the flash-attn
package for Python 3.14. So far, I can only get this to run on Python 3.12 without have to pull-in massive CUDA
libraries from source. More setup details below.

### Setup (Python 3.12 + uv)

flash-attn is required just to load the checkpoint (the pickled attention layers reference `flash_attn` functions),
and prebuilt wheels only exist for specific (CUDA, torch, Python) combos — `cu13 + torch2.9 + cp312` below. Its
setup.py crashes without `nvcc` before it ever checks for a prebuilt wheel, so install the wheel directly by URL
rather than by package name.

```bash
uv python install 3.12
uv venv --python 3.12 ~/.venv-aifs
source ~/.venv-aifs/bin/activate

uv pip install torch==2.9.1 --index-url https://download.pytorch.org/whl/cu130
uv pip install "anemoi-inference[huggingface]==0.8.3" anemoi-models==0.11.2 anemoi-utils==0.4.35.post3
uv pip install earthkit-regrid==0.5.1 ecmwf-opendata==0.3.29 "earthkit-data<1.0.0" structlog
uv pip install https://github.com/Dao-AILab/flash-attention/releases/download/v2.8.3/flash_attn-2.8.3%2Bcu13torch2.9cxx11abiTRUE-cp312-cp312-linux_x86_64.whl

# verify the compiled kernel loads
python -c "from flash_attn import flash_attn_func; import flash_attn; print(flash_attn.__version__)"
```

### Running

Downloads are split out of the inference script so a forecast run never re-downloads anything:

```bash
# 1. Prefetch -- always run this first. Each step is skipped when already current:
#    the 2.55 GB checkpoint from HuggingFace (ecmwf/aifs-ens-2.0, cached
#    venv-independently in ~/.cache/huggingface), the AIFS open data initial conditions
#    (saved to aifs_ens_input_state.npz, ~1 GB), and the IFS HRES 3-hourly ssrd fields
#    (saved to ifs_hres_ssrd.npz, ~75 MB).
python example_ecmwf_aifs_ens_prefetch.py

# 2. Forecast scripts -- no network needed. These are independent of each other:
#    each reads only its own prefetched artifact, so run either one, both in any
#    order, or just one; re-run them freely off a single prefetch.
python example_ecmwf_aifs_ens_solar.py   # AIFS ENS model inference (GPU): 6-hourly SSRD + hourly via disaggregation
python example_ecmwf_ifs_hres_solar.py   # IFS HRES postprocessing (CPU): hourly SSRD via disaggregation
```

The prefetch checks before downloading: the checkpoint is resolved offline against the local HuggingFace cache
first, and the open data is only re-fetched when a newer cycle (00/06/12/18 UTC) is fully published than the one
already saved. The inference script warns when the saved cycle is more than 12 h old.

### Open data source nuances

The initial conditions come from ECMWF open data, which is served from the direct portal plus three cloud mirrors
(the `SOURCE` constant in `example_ecmwf_aifs_ens_prefetch.py`). Each has quirks:

- `ecmwf` — the direct portal; aggressively rate-limited (429s), especially right after a new cycle publishes.
- `google` — buggy with this toolchain: multiurl (<= 0.3.9) special-cases AWS/Azure for single-range requests but
  not GCS, so it sends multi-range requests that GCS rejects with 400 `InvalidArgument`.
- `aws` — works, but intermittently throttles with `503 Slow Down` around fresh cycle publication.
- `azure` — works; the most reliable so far, and the current default.

A related nuance handled by the prefetch: the `oper`/`enfo`/`waef` streams publish on their own schedules after
each cycle, so the "latest" cycle is taken as the most recent one available across all three — otherwise retrievals
404 in the window right after a new cycle starts publishing.

Publication schedule: cycles run at 00/06/12/18 UTC daily. Real-time dissemination of a cycle starts ~5 h 45 m
after its nominal time (e.g. the 12z HRES starts publishing at 17:45 UTC), with steps arriving progressively and
the ensemble/wave streams completing later; in practice the full cross-stream set reaches the open-data mirrors
roughly 7.5–8 h after cycle time (observed: the 12z ensemble landed ~19:40–20:00 UTC). Forecast steps differ by
cycle: 00/12 UTC provide 3-hourly steps to 144 h (then 6-hourly to 240 h); 06/18 UTC only go to 90 h.

### Hourly granularity and temporal disaggregation

AIFS ENS 2.0 advances the atmosphere in fixed 6-hour steps — it was trained on t−6h/t0 → t+6h transitions and has
no variable lead-time mechanism (unlike Aurora 1.5's `fine_lead_times`), so 6-hourly is its finest native output.
Its `ssrd` is accumulated over each step, i.e. a 6 h-mean SSRD flux.

For hourly values, `example_ecmwf_ifs_hres_solar.py` combines two techniques:

1. **Physics-based sub-6h signal**: the IFS HRES `ssrd` forecast from open data (3-hourly steps, downloaded by the
   prefetch into `ifs_hres_ssrd.npz`; accumulated since forecast start, so consecutive steps are differenced into
   per-window energies). Cloud timing within the day comes from the IFS radiation scheme itself, so this holds up
   in persistently cloudy regions — it is not a clear-sky assumption.
2. **Clear-sky temporal disaggregation** (pvlib, Haurwitz model — chosen because it needs no turbidity tables):
   each 3 h window's energy is split across its hours proportional to the clear-sky irradiance profile. This is
   energy-preserving and restores the diurnal shape; the one thing it cannot represent is cloud *evolution within*
   a 3 h window (e.g. fog burning off mid-window is smeared across it).

Requires `uv pip install pvlib` on top of the setup above. The AIFS inference script applies the same
disaggregation to its own 6 h windows as a post-processing step (importing `disaggregate_window` from the IFS
script), so both pipelines end in hourly values — the difference is cloud timing: AIFS smears it across 6 h
windows, IFS HRES across 3 h windows. Looping AIFS over ensemble members would additionally give probabilistic
hourly values.
