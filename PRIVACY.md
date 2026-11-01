# Privacy and data handling

Language Edge performs image generation, VAE encoding and map calculations on your machine. It has no hosted inference endpoint, app analytics, email integration or automatic sharing action. Hugging Face telemetry is disabled by default before model libraries are imported.

## Network activity

Package installation contacts package indexes. Downloading models contacts Hugging Face and its storage providers; they receive normal connection details and requested model filenames. Prompts and images are passed to local model pipelines, not included in those download requests. Cached local model folders can be used without online model downloads. Authentication tokens, if needed, belong in your environment or Hugging Face's user cache, never in this repository.

## What is saved

Workspaces store prompt text, seeds, model/configuration information, generated images, imported image copies, fingerprints, neighbour scores, and the saved map. Model caches may reside in your user cache separately. Map JSON exports include prompts and filenames; a complete run bundle includes images and fingerprints. Fingerprints are derived image data and are not anonymous. Review everything before sharing.

Uploaded PNG/JPEG/WebP files are decoded, orientation-corrected and saved as metadata-free RGB PNG copies. Served image copies omit EXIF, GPS, comments and ICC metadata. This does not anonymize visible people, locations, text or other content in the pixels. Files you import by CLI remain untouched at their original location. Older stored image copies from before this hardening were not retroactively rewritten.

## Location and cloud sync

New browser workspaces default to local application data: `%LOCALAPPDATA%\LanguageEdge\runs` on Windows, `~/Library/Application Support/LanguageEdge/runs` on Mac, or the XDG data directory on Linux. `LANGUAGE_EDGE_DATA` and `serve --data PATH` override this.

Existing `runs/` folders are not moved or deleted. Any selected OneDrive, iCloud, Dropbox, network or backed-up folder may be copied elsewhere by that service independently of this app. Operating-system backups can also include application data. Local processing is not a promise that your machine's backup services never upload files.

## GitHub and release packages

Private runs, model weights, environment files, keys and administrative files are excluded from normal Git tracking. Ignore rules are not access control and cannot remove files already committed. Do not force-add private data. The release builder uses an explicit allowlist, checks the frozen public demo checksum and scans its output for common credential patterns. It never rebuilds examples from live user runs.

The public demo contains only project-created example prompts and generated images. Local Word planning documents are kept outside the current public source file list. Removing files from the current tree does not purge Git history: earlier planning notes and commit author identities remain in history. Git commit author names and project license attribution are public when a repository is published. Pattern scanning cannot prove absence of every type of private data; inspect new content before release.

## Deletion and access

Deleting an entire workspace directory removes that workspace's local files. This does not delete source images, model caches, cloud copies or backups. No encryption is provided by the application. Other processes running as your operating-system user may access files or the local server. Use an appropriate OS account and disk protection for sensitive projects.
