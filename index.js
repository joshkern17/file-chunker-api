import express from "express";
import multer from "multer";
import fs from "fs";
import mammoth from "mammoth";
import pdfParse from "pdf-parse";

const app = express();
const upload = multer({ dest: "/tmp" });

app.post("/extract", upload.single("file"), async (req, res) => {
  try {
    const { file } = req;
    if (!file) return res.status(400).json({ error: "No file" });

    let rawText = "";
    switch (file.mimetype) {
      case "application/pdf": {
        const data = await pdfParse(fs.readFileSync(file.path));
        rawText = data.text;
        break;
      }
      case "application/vnd.openxmlformats-officedocument.wordprocessingml.document": {
        const { value } = await mammoth.extractRawText({ buffer: fs.readFileSync(file.path) });
        rawText = value;
        break;
      }
      case "text/plain":
        rawText = fs.readFileSync(file.path, "utf-8");
        break;
      default:
        return res.status(415).json({ error: `Unsupported type ${file.mimetype}` });
    }

    const paras = rawText.split(/\n\s*\n/).map(p => p.trim()).filter(p => p.length > 40);
    const chunks = [];
    for (let i = 0; i < paras.length; i += 3)
      chunks.push(paras.slice(i, i + 3).join("\n\n"));

    res.json({ chunk_count: chunks.length, chunks });
  } catch (e) {
    console.error(e);
    res.status(500).json({ error: "Parse error" });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log("Listening on", PORT));
