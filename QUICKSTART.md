# Start here

Language Edge makes a reference map from images generated using your prompts. You can then add other images and explore how their VAE fingerprints compare with that reference. An SAE is not required.

## Try the demo first

Extract the source package. Install Python 3.11 and follow the Windows or Mac setup instructions in README.md. Run the setup script once, then the start script. Setup installs the prebuilt demo, which you can select in Reference workspace without generating anything.

Windows: `Setup Windows.cmd`, then `Start Windows.cmd`.

Mac: see README.md for the Terminal commands to enable and run `Setup Mac.command` and `Start Mac.command`. Mac GPU execution is not yet hardware-verified.

## Make your own map

1. Click **New workspace**, choose a name and your model. For Stable Diffusion 1.5, choose that model.
2. Click **Download example prompts** to see the format. Start with a small collection before using thousands. A CSV needs a `prompt` column, with one prompt per row.
3. Choose your prompt file and leave the seed at 42 for the first test. Click **Generate reference images**. The program generates images and encodes them; first use may download several GB of model weights.
4. When generation and encoding finish, click **Build the 3D map**. The saved reference stays fixed.
5. Under **Explore more images**, import image files or write a new prompt and click **Generate and place**.
6. Drag to rotate, scroll to zoom, and click a point to inspect its image, nearest reference examples, and novelty score.

## Read it simply

The wireframe illustrates your reference collection in 3D. A high novelty score means an image differs more from nearby reference fingerprints in the original space. The 3D view can hide some differences, and VAE fingerprints are sensitive to composition and shifts. This is an experimental explorer of sampled coverage, not proof of a universal language boundary.

Each model has its own map. Processing and the browser interface run locally; installation and model downloads require internet. New workspaces default to local application data outside the repository. Cloud backup/sync software can still copy any chosen folder independently; see PRIVACY.md. A GPU is recommended for generation, with a current compatible PyTorch build and driver. Mac hardware and upgraded-stack GPU verification are pending.
