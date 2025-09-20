import express from 'express';
import cors from 'cors';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { Low } from 'lowdb';
import { JSONFile } from 'lowdb/node';
import nodemailer from 'nodemailer';
import dotenv from 'dotenv';
import OpenAI from 'openai';

// --- INITIALISIERUNG ---
dotenv.config();
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const file = join(__dirname, 'db.json');
const adapter = new JSONFile(file);
const db = new Low(adapter, { tags: [], articles: [], subscriptions: [] });
await db.read();

// OpenAI-Client initialisieren
const openai = new OpenAI({
    apiKey: process.env.OPENAI_API_KEY,
});

// Nodemailer Transporter
const transporter = nodemailer.createTransport({
    service: 'gmail',
    auth: {
        user: process.env.EMAIL_SENDER,
        pass: process.env.EMAIL_PASSWORD,
    },
});

async function sendNotificationEmail(recipient, article) {
    console.log(`Sende E-Mail für Artikel "${article.title}" an ${recipient}...`);
    try {
        await transporter.sendMail({
            from: `"MarketRooster" <${process.env.EMAIL_SENDER}>`,
            to: recipient,
            subject: `MarketRooster Alert: ${article.title}`,
            text: `Ein neuer Artikel passt zu Ihren Kriterien:\n\nTitel: ${article.title}\nQuelle: ${article.source}\nZusammenfassung: ${article.summary}\nLink: ${article.url}`,
            html: `<p>Ein neuer Artikel passt zu Ihren Kriterien:</p><h3>${article.title}</h3><p><strong>Quelle:</strong> ${article.source}</p><p><strong>Zusammenfassung:</strong> ${article.summary}</p><a href="${article.url}">Zum Artikel</a>`,
        });
        console.log(`E-Mail an ${recipient} erfolgreich gesendet.`);
    } catch (error) {
        console.error(`Fehler beim Senden der E-Mail an ${recipient}:`, error);
    }
}

// --- SERVER SETUP ---
const app = express();
const PORT = 3001;
app.use(cors({ origin: 'http://localhost:3000' }));
app.use(express.json());

// --- API ROUTES ---
app.get('/api/articles', (req, res) => res.json(db.data.articles));
app.get('/api/tags', (req, res) => res.json(db.data.tags));

app.post('/api/subscribe', async (req, res) => {
    try {
        const { email, tags, priorities } = req.body;
        if (!email) return res.status(400).json({ message: 'Email is required.' });
        db.data.subscriptions = db.data.subscriptions || [];
        const { subscriptions } = db.data;
        const newSubscription = {
            id: subscriptions.length > 0 ? Math.max(...subscriptions.map(s => s.id)) + 1 : 1,
            email, tags, priorities, notifiedArticleIds: [],
        };
        subscriptions.push(newSubscription);
        await db.write();
        res.status(201).json({ message: 'Subscription successful!' });
    } catch (error) {
        console.error("Server error during subscription:", error);
        res.status(500).json({ message: "Server error during subscription." });
    }
});

app.post('/api/approved', async (req, res) => {
    try {
        const { approvedText } = req.body;
        if (!approvedText) return res.status(400).json({ message: 'Approved text is required.' });
        const approvedFile = join(__dirname, 'approved.json');
        const approvedAdapter = new JSONFile(approvedFile);
        const approvedDb = new Low(approvedAdapter, []);
        await approvedDb.read();
        approvedDb.data = approvedDb.data || [];
        approvedDb.data.push({
            id: approvedDb.data.length > 0 ? Math.max(...approvedDb.data.map(item => item.id)) + 1 : 1,
            text: approvedText,
            approvedAt: new Date().toISOString()
        });
        await approvedDb.write();
        console.log('[Backend] Neuer Text wurde akzeptiert und gespeichert.');
        res.status(201).json({ message: 'Text successfully approved and saved.' });
    } catch (error) {
        console.error('[Backend] FEHLER beim Speichern des akzeptierten Textes:', error);
        res.status(500).json({ message: 'Server error while saving approved text.' });
    }
});

app.post('/api/tags/process', async (req, res) => {
    try {
        const { name: newTagName } = req.body;
        if (!newTagName) return res.status(400).json({ message: 'Tag name is required.' });
        const { tags, articles } = db.data;
        db.data.subscriptions = db.data.subscriptions || [];
        const { subscriptions } = db.data;
        const searchTerm = newTagName.toLowerCase();
        const searchRegex = new RegExp(`\\b${searchTerm}\\b`, 'i');
        const tagExists = tags.some(tag => tag.name.toLowerCase() === searchTerm);
        if (!tagExists) {
            tags.push({ id: tags.length > 0 ? Math.max(...tags.map(t => t.id)) + 1 : 1, name: newTagName });
        }
        articles.forEach(article => {
            const content = `${article.title} ${article.summary} ${article.context} ${article.draftText}`;
            article.tags = article.tags || [];
            if (searchRegex.test(content) && !article.tags.includes(newTagName)) {
                article.tags.push(newTagName);
            }
        });
        const checkMatch = (article, sub) => {
            const priorityMatch = !sub.priorities.length || sub.priorities.includes(article.priority);
            const tagMatch = !sub.tags.length || sub.tags.some(tag => article.tags.includes(tag));
            return priorityMatch && tagMatch;
        };
        for (const article of articles) {
            for (const sub of subscriptions) {
                const hasBeenNotified = sub.notifiedArticleIds.includes(article.id);
                if (!hasBeenNotified && checkMatch(article, sub)) {
                    await sendNotificationEmail(sub.email, article);
                    sub.notifiedArticleIds.push(article.id);
                }
            }
        }
        await db.write();
        res.status(200).json({ updatedArticles: articles, allTags: tags });
    } catch (error) {
        console.error("Error processing tag:", error);
        res.status(500).json({ message: "Server error while processing tag." });
    }
});

app.post('/api/draft/combine', async (req, res) => {
    const { existingText, newText } = req.body;
    if (!existingText) {
        return res.json({ combinedText: newText });
    }
    const prompt = `Du bist ein professioneller Redakteur. Deine Aufgabe ist es, zwei Textabschnitte zu einem einzigen, flüssigen und kohärenten Text zu verschmelzen. Kombiniere die Kernaussagen, vermeide Wiederholungen und sorge für einen natürlichen Lesefluss. Gib NUR den finalen, kombinierten Text zurück, ohne jegliche Einleitung, Kommentare oder Anführungszeichen.

Bestehender Text:
---
${existingText}
---

Neuer Text, der hinzugefügt werden soll:
---
${newText}
---

Kombinierter Text:`;

    try {
        const completion = await openai.chat.completions.create({
            model: "gpt-3.5-turbo",
            messages: [{ role: "user", content: prompt }],
            temperature: 0.5,
        });
        const combinedText = completion.choices[0].message.content.trim();
        res.json({ combinedText });
    } catch (error) {
        console.error("Fehler bei der OpenAI API-Anfrage:", error);
        res.status(500).json({ message: "Fehler bei der Kommunikation mit der OpenAI API." });
    }
});

// --- SERVER START ---
app.listen(PORT, () => {
  console.log(`Backend server is running on http://localhost:${PORT}`);
});