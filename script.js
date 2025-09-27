const BACKEND_URL = "http://127.0.0.1:5000";

const downloadBtn = document.getElementById("downloadBtn");
const status = document.getElementById("status");
const youtubeUrlInput = document.getElementById("youtubeUrl");
const qualitySelect = document.getElementById("qualitySelect");
const spinner = document.getElementById("spinner");

downloadBtn.addEventListener("click", async () => {
  const url = youtubeUrlInput.value.trim();
  const quality = qualitySelect.value;

  if (!url) {
    status.innerText = "Paste a YouTube URL first";
    return;
  }

  // Preparing state
  downloadBtn.disabled = true;
  downloadBtn.innerText = "Preparing…";
  spinner.style.display = "block"; // Show spinner
  status.innerText = "";

  try {
    const res = await fetch(`${BACKEND_URL}/download`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ url, quality }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ error: "Failed" }));
      throw new Error(err.error || "Download failed");
    }

    downloadBtn.innerText = "Downloading…";

    const reader = res.body.getReader();
    const contentLength = +res.headers.get("Content-Length") || 0;
    let receivedLength = 0;
    const chunks = [];

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      chunks.push(value);
      receivedLength += value.length;

      if (contentLength) {
        status.innerText = `Downloading…`;
      } else {
        status.innerText = `Downloading… ${Math.round(
          receivedLength / 1024
        )} KB`;
      }
    }
    // Combine chunks and download
    const blob = new Blob(chunks);
    let filename = "video.mp4";
    const cd = res.headers.get("content-disposition");
    if (cd && cd.indexOf("filename=") !== -1) {
      filename = cd.split("filename=")[1].replace(/"/g, "");
    }

    const downloadUrl = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = downloadUrl;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    a.remove();
    URL.revokeObjectURL(downloadUrl);

    // Success
    status.innerText = "Download completed!";
    youtubeUrlInput.value = "";
  } catch (err) {
    status.innerText = "Error: " + (err.message || err);
  } finally {
    spinner.style.display = "none"; // Hide spinner
    downloadBtn.disabled = false;
    downloadBtn.innerText = "Download";
  }
});
