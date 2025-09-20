import express from 'express';
import cors from 'cors';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { Low } from 'lowdb';
import { JSONFile } from 'lowdb/node';

const app = express();
const PORT = 3001;

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const file = join(__dirname, 'db.json');

const adapter = new JSONFile(file);
const db = new Low(adapter, { tags: [], articles: [] });

app.use(cors());
app.use(express.json());

const readData = async () => {
  await db.read();
  db.data = db.data || { tags: [], articles: [] };
  db.data.tags = db.data.tags || [];
  db.data.articles = db.data.articles || [];
  return db.data;
};

// --- API ROUTES ---

app.get('/api/articles', async (req, res) => {
  const data = await readData();
  res.json(data.articles);
});

app.get('/api/tags', async (req, res) => {
  const data = await readData();
  res.json(data.tags);
});

app.post('/api/tags/process', async (req, res) => {
    try {
        const { name: newTagName } = req.body;
        console.log(`[Backend] Received request to process new tag: "${newTagName}"`); // DEBUGGING LOG

        if (!newTagName) {
            return res.status(400).json({ message: 'Tag name is required.' });
        }

        const data = await readData();
        const searchTerm = newTagName.toLowerCase();
        
        // VERBESSERTE LOGIK: Regex für die Suche nach ganzen Wörtern, case-insensitive
        const searchRegex = new RegExp(`\\b${searchTerm}\\b`, 'i');

        const tagExists = data.tags.some(tag => tag.name.toLowerCase() === searchTerm);
        let newTagObject = null;
        if (!tagExists) {
            newTagObject = {
                id: data.tags.length > 0 ? Math.max(...data.tags.map(t => t.id)) + 1 : 1,
                name: newTagName
            };
            data.tags.push(newTagObject);
        } else {
            newTagObject = data.tags.find(tag => tag.name.toLowerCase() === searchTerm);
        }

        data.articles.forEach(article => {
            const content = `${article.title} ${article.summary} ${article.context} ${article.draftText}`;
            article.tags = article.tags || [];

            // Teste mit der neuen Regex anstelle von .includes()
            if (searchRegex.test(content) && !article.tags.includes(newTagName)) {
                article.tags.push(newTagName);
            }
        });

        await db.write();
        console.log('[Backend] Processing complete. Sending success response.'); // DEBUGGING LOG

        res.status(200).json({ 
            newTag: newTagObject,
            updatedArticles: data.articles,
            allTags: data.tags
        });
    } catch (error) {
        console.error("[Backend] CRITICAL ERROR while processing tag:", error);
        res.status(500).json({ message: "An internal server error occurred." });
    }
});

app.listen(PORT, () => {
  console.log(`Backend server is running on http://localhost:${PORT}`);
});