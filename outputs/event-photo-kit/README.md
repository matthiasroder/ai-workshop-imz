# Event Photo Kit

Turn event photos into 1080 × 1920 Story JPGs and an image-only web gallery. Use your own event details, photos and website.

## Try it locally

1. Install [uv](https://docs.astral.sh/uv/getting-started/installation/) and unzip the kit.
2. Open a terminal in `event-photo-kit`. Edit `event.toml` with your event title, slug, date and city.
3. Put photos in `photos/`. For Google Drive, set `input.drive_folder` to a folder shared as **Anyone with the link**. The kit reads photos directly inside that folder.
4. Run `uv run event_photos.py`. Open `output/<your-slug>/site/index.html` in a browser. The Story JPGs are in `site/photos/`.

The kit draws a simple event overlay. To use your own design, set `event.overlay` to the path to a transparent 1080 × 1920 PNG. Use a different slug for each event. Existing images stay in the stream when their source files are removed.

## Save finished JPGs in Google Drive

With [Google Drive for desktop](https://www.google.com/drive/download/) running, create an `output` folder in your event folder. In `event.toml`, set `output.drive_sync_directory` to the full path to that synced folder as shown in Finder or File Explorer. Use forward slashes in the TOML path, including on Windows. Each run copies the finished JPGs there and Drive syncs them. `--watch` does this every minute. Captions stay in the local `captions/` folder.

## Put it on your website

**Any static host.** Copy the contents of `output/<your-slug>/site/` into a dedicated folder on your site. Upload that folder again when you add photos.

**Automatic updates with GitHub Pages.** Install [GitHub CLI](https://cli.github.com/) and run `gh auth login`. Use a repository and branch you control. In `event.toml`, set `website.repository`, `website.branch` and a dedicated `website.path`. For example, with Pages publishing `main` from `/docs`, use `docs/events/your-event` as the path. Enable Pages in the repository’s **Settings → Pages** after the first upload creates the `docs` folder, if needed. For a site with its own deploy workflow, put the event folder inside that workflow’s static asset directory. [GitHub Pages setup](https://docs.github.com/en/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site)

```sh
uv run event_photos.py --publish
```

To check for new photos every minute, leave this running in a terminal on an awake computer. Press **Ctrl+C** to stop.

```sh
uv run event_photos.py --watch --publish
```

Use `--watch` alone to update the local gallery. Repeated runs skip existing photos. Uploads preserve gallery order and use your GitHub login. Pages may take a moment to deploy after each update.

## Instagram Stories and optional captions

Save a JPG to your phone and select it in Instagram under **+ → Story**. If you want caption drafts, set your own `OPENAI_API_KEY` environment variable and run:

```sh
uv run event_photos.py --captions
```

This sends each finished JPG and the event details to OpenAI. The model and language are configurable under `[captions]`. Drafts go to `output/<your-slug>/captions/`, outside the website folder. Paste the text in Instagram with **Aa**. Posting to Instagram happens in the app.
