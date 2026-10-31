from pathlib import Path
from docx import Document
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
doc = Document()
sec = doc.sections[0]
sec.page_height, sec.page_width = Inches(11.7), Inches(8.3)
sec.top_margin = sec.bottom_margin = Inches(.75)
sec.left_margin = sec.right_margin = Inches(.8)
for name in ['Normal', 'Title', 'Subtitle', 'Heading 1', 'Heading 2']:
    st = doc.styles[name]
    st.font.name = 'Calibri'
    st.font.color.rgb = RGBColor(0, 0, 0)
doc.styles['Normal'].font.size = Pt(11)
doc.styles['Normal'].paragraph_format.space_after = Pt(7)
doc.styles['Title'].font.size = Pt(26)
doc.styles['Heading 1'].font.size = Pt(16)
doc.styles['Heading 2'].font.size = Pt(12)
doc.core_properties.title = 'Language Edge Project Plan and Changelog'
doc.core_properties.author = 'Art'
for style in doc.styles:
    for border in list(style.element.iter('{http://schemas.openxmlformats.org/wordprocessingml/2006/main}pBdr')):
        border.getparent().remove(border)

def p(text, style=None):
    doc.add_paragraph(text, style)
def h(text):
    doc.add_heading(text, 1)
def item(title, body):
    doc.add_heading(title, 2)
    p(body)

doc.add_heading('Language Edge Project Plan and Changelog', 0)
p('Version 1.1   |   31 October 2026', 'Subtitle')
p('We will build a standalone toolkit that turns a user supplied prompt collection into a fixed 3D reference map, then places existing and newly generated images into that same map. The intended audience includes artists exploring image collections and regions their sampled prompts have not covered.')
h('Agreed approach')
p('Use the chosen generation model\u2019s VAE encoder to represent finished images. No SAE or intermediate generation step capture is required. Start with Stable Diffusion XL Turbo and Stable Diffusion 1.5, subject to compatibility and license checks. Each model and encoding configuration has a separate reference map.')
item('Phase one Build the reference map', 'Import CSV or JSONL prompts, generate reference images, and encode the finished images with deterministic VAE encoding and fixed preprocessing. Fit PCA on reference representations only and save the transformation. Display the reference points and an optional blue mesh illustrating sampled coverage in 3D.')
item('Phase two Explore additional images', 'Import existing image files or generate new images. Encode them with the same VAE and preprocessing, then apply the saved projection. Show each image, its nearest reference examples, metadata, and a novelty score measured against the reference in the original representation.')
h('Meaning of the map')
p('The blue mesh is an illustrative surface in the compressed 3D view. It is not an exact boundary in the full latent space. Novelty means difference from the sampled reference collection; it is not proof that an image cannot be generated with language. PCA loses information, so visual proximity can disagree with full dimensional distance.')
p('VAE distances are not yet validated for the artistic groupings we want. A small pilot must test their usefulness before this representation is treated as established. The finished image encoding is also distinct from the exact latent trajectory that originally produced the image.')

doc.add_page_break()
h('Execution plan')
item('1 Audit and compatibility', 'Review reusable Terra Obscura code, dependencies, licenses, attribution, available hardware, and both proposed model interfaces. Identify Windows and macOS execution paths without assuming that preparation on Windows verifies Mac support.')
item('2 Define and test the representation', 'Specify resolution, resize and crop behavior, deterministic VAE encoding, latent scaling, vectorization, and distance metric. Compare a small set of sensible choices using repeated encodings and visually related and unrelated examples. Check whether position or small crop changes dominate useful similarity.')
item('3 Lock the reference protocol', 'Deduplicate prompts and define reference, calibration, and evaluation splits before generation. Keep related prompt seeds together. Record seeds, generation settings, model and VAE versions, preprocessing, and dataset identity. Calibrate scores using held out data.')
item('4 Build reliable capture', 'Implement CSV and JSONL input, generation, image encoding, incremental storage, progress reporting, and resumable runs. Benchmark a small batch before estimating a 10000 prompt run. Batch distance calculations to avoid unbounded memory use.')
item('5 Save stable reference bundles', 'Package reference vectors, PCA parameters, normalization, calibration, configuration, and provenance. Reject incompatible additions. Adding test images must not refit PCA or change the reference threshold; rebuilding creates a new version.')
item('6 Adapt and lightly polish the viewer', 'Reuse the existing viewer where practical. Add reference selection, prompt and image import, generation progress, clickable image points, nearest examples, novelty scores, and retained PCA variance. Keep the optional blue mesh visually distinct from the numerical coverage score.')
item('7 Validate and publish', 'Run a small pilot using our own prompts, then expand the example collection after feasibility checks. Verify supported Windows and Mac paths, installation, and recovery. Prepare a Python package, browser UI, launch instructions, small example prompt set, prebuilt demo, methods, and licensing. Publish after release authorization.')

doc.add_page_break()
h('Scope and working arrangements')
p('One shared Python backend and browser interface, with platform specific launchers. Design model adapters for extension while initially testing two models. SAE features and intermediate activation maps are deferred advanced modes. A native desktop application, hosted GPU service, and cross model coordinate alignment are outside the first release.')
p('Keep project documents, code, examples, tests, and reports in this Language Edge folder. Keep private prompts, generated data, model weights, and credentials out of Git. Large derived data may need an explicitly configured local data directory because latent storage and OneDrive synchronization can become substantial.')
h('Input needed later')
p('No additional input or private dataset is needed for development and the example pilot. Later dependencies are access to any gated model assets, authorization before paid compute, Mac hardware or a test runner for verification, and the GitHub destination and publication authorization. The user should judge whether the resulting neighborhoods are artistically useful.')
h('Schedule')
p('Earlier planning suggested roughly 8 to 12 focused working days for a narrow beta. This is provisional, not a commitment: the representation changed to finished image VAE latents after that estimate. Reestimate after the audit and benchmark, including storage, GPU availability, and Mac compatibility. Large generation runs are additional elapsed compute time.')
h('Changelog')
item('30 October 2026 Version 1.0', 'Created this project plan and designated the Language Edge project folder. Recorded the two phase reference and image exploration workflow; VAE encoding as the proposed first representation; optional illustrative blue mesh; SDXL Turbo and SD 1.5 as initial model targets; Windows and macOS support; and a validation checkpoint before full implementation.')
p('Design history: earlier discussion considered SAE features, direct generation activations, and external image embeddings. The latest agreed direction uses finished image VAE encodings to accommodate existing image files. Terra Obscura\u2019s current SAE map is a source of reusable tooling, not validation of this new representation.')
p('Status on 30 October: planning documentation created; implementation and verification had not yet been completed. Subsequent progress is recorded on the following page.')

doc.add_page_break()
h('Implementation update')
p('31 October 2026   |   Version 0.1.0 local beta')
p('A working local toolkit now implements the two phase workflow. It uses our own example prompts and does not require the friend\u2019s dataset. The viewer is served locally at http://127.0.0.1:8877 and can be reopened with Start Windows.cmd.')
item('Completed implementation', 'Created the independent Python package, two model adapters, deterministic VAE encoding, prompt import and grouped splits, resumable generation, image import, frozen reference bundles, full dimensional novelty, reference only PCA, and a lightly polished 3D viewer. The optional blue envelope is explicitly a convex hull of projected reference points. Windows and Mac launchers, a precomputed demo, setup instructions, methods, notices and core test workflow are included.')
item('Measured local verification', 'SDXL Turbo generated and encoded 36 collection images, plus four query generations and one imported image. Stable Diffusion 1.5 generated and encoded 12 collection images, plus four query generations and one import. Seven automated core tests and desktop and mobile browser checks pass on Windows. Real stop and resume, duplicate prevention and unchanged reference bytes passed for both models. Browser upload and query job checks also passed; numerical results are in the reports folder.')
item('Representation finding', 'SDXL Turbo re-encoding was exactly repeatable in the small CUDA pilot. The 3D projection retained about 40.7 percent of reference variation and recovered about 62.2 percent of full space nearest neighbors. An 8 pixel image shift caused substantial changes, and two seed comparisons also differed substantially. These findings support a repeatable experimental VAE explorer, not a validated semantic map or a proven language boundary.')
item('Distribution and remaining verification', 'The source release and demo are prepared locally; model weights and private run folders are excluded. Mac hardware execution, remote CI, 10000 prompt performance, large held out calibration and artistic usefulness remain unverified. Public GitHub publication needs a destination and account access. The proposed MIT code license does not replace model terms.')
h('Maintaining this record')
p('CHANGELOG.md tracks source changes. The reports folder contains the audit, numerical pilot measurements and integration results. This Word document is the readable plan and project summary. Add dated entries when behavior, evidence, scope or release status changes; do not mark planned or unverified work as complete.')

out = ROOT / 'Language Edge Plan and Changelog.docx'
doc.save(out)
print(out)
