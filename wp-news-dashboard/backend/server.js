import express from 'express';
import cors from 'cors';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { Low } from 'lowdb';
// KORREKTUR HIER: JSONFile wird von 'lowdb/node' importiert
import { JSONFile } from 'lowdb/node';

const app = express();
const PORT = 3001;

// Setup lowdb für ES Modules
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const file = join(__dirname, 'db.json');

const adapter = new JSONFile(file);
// Initialisiere die DB mit Standardwerten, falls die Datei leer ist
const db = new Low(adapter, { tags: [], articles: [] }); 

// Middleware
app.use(cors());
app.use(express.json());

// Helper function to read data
const readData = async () => {
  await db.read();
  return db.data;
};

// --- API ROUTES ---

// GET all articles
app.get('/api/articles', async (req, res) => {
  const data = await readData();
  res.json(data.articles);
});

// GET all tags
app.get('/api/tags', async (req, res) => {
  const data = await readData();
  res.json(data.tags);
});

// POST a new tag
app.post('/api/tags', async (req, res) => {
  const newTag = req.body;
  const data = await readData();
  newTag.id = data.tags.length > 0 ? Math.max(...data.tags.map(t => t.id)) + 1 : 1;
  data.tags.push(newTag);
  await db.write();
  res.status(201).json(newTag);
});

app.listen(PORT, () => {
  console.log(`Backend server is running on http://localhost:${PORT}`);
});