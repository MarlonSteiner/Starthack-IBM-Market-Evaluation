import express from 'express';
import cors from 'cors';
import { join, dirname } from 'path';
import { fileURLToPath } from 'url';
import { Low } from 'lowdb';
import { JSONFile } from 'lowdb/node';
import nodemailer from 'nodemailer'; // NEU
import dotenv from 'dotenv'; // NEU

// --- INITIALISIERUNG ---
dotenv.config(); // Lade .env-Datei
const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const file = join(__dirname, 'db.json');

const adapter = new JSONFile(file);
const db = new Low(adapter, { tags: [], articles: [], subscriptions: [] });
await db.read(); // Lese DB einmal beim Start

// NEU: E-Mail Transporter mit Nodemailer konfigurieren
const transporter = nodemailer.createTransport({
    service: 'gmail', // oder ein anderer SMTP-Provider
    auth: {
        user: process.env.EMAIL_SENDER,
        pass: process.env.EMAIL_PASSWORD,
    },
});

// NEU: E-Mail-Funktion
async function sendNotificationEmail(recipient, article) {
    console.log(`Sende E-Mail für Artikel "${article.title}" an ${recipient}...`);
    try {
        await transporter.sendMail({
            from: `"MarketRooster" <${process.env.EMAIL_SENDER}>`,
            to: recipient,
            subject: `MarketRooster Alert: ${article.title}`,
            text: `Ein neuer Artikel passt zu Ihren Kriterien:\n\nTitel: ${article.title}\nQuelle: ${article.source}\nZusammenfassung: ${article.summary}\nLink: ${article.url}`,
            html: `<p>Ein neuer Artikel passt zu Ihren Kriterien:</p>
                   <h3>${article.title}</h3>
                   <p><strong>Quelle:</strong> ${article.source}</p>
                   <p><strong>Zusammenfassung:</strong> ${article.summary}</p>
                   <a href="${article.url}">Zum Artikel</a>`,
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

// Route zum Speichern von Abonnements
app.post('/api/subscribe', async (req, res) => {
    try {
        const { email, tags, priorities } = req.body;
        if (!email) return res.status(400).json({ message: 'Email is required.' });

        const { subscriptions } = db.data;
        const newSubscription = {
            id: subscriptions.length > 0 ? Math.max(...subscriptions.map(s => s.id)) + 1 : 1,
            email,
            tags,
            priorities,
            notifiedArticleIds: [], // NEU: Liste zur Nachverfolgung
        };
        subscriptions.push(newSubscription);
        await db.write();

        res.status(201).json({ message: 'Subscription successful!' });
    } catch (error) {
        res.status(500).json({ message: "Server error during subscription." });
    }
});

// Route zum Verarbeiten von Tags (wird zum E-Mail-Trigger)
app.post('/api/tags/process', async (req, res) => {
    try {
        // ... (Der Code zum Hinzufügen von Tags bleibt gleich)
        const { name: newTagName } = req.body;
        if (!newTagName) return res.status(400).json({ message: 'Tag name is required.' });
        
        const { tags, articles, subscriptions } = db.data;
        // ... (Logik zur Tag-Erstellung und Zuweisung)

        // START: E-MAIL-LOGIK nach der Tag-Verarbeitung
        console.log("Prüfe auf neue Benachrichtigungen nach Tag-Update...");

        // Die Logik, die prüft, ob ein Artikel passt
        const checkMatch = (article, sub) => {
            const priorityMatch = !sub.priorities.length || sub.priorities.includes(article.priority);
            const tagMatch = !sub.tags.length || sub.tags.some(tag => article.tags.includes(tag));
            return priorityMatch && tagMatch;
        };
        
        // Gehe durch alle Artikel und Abos
        for (const article of articles) {
            for (const sub of subscriptions) {
                const hasBeenNotified = sub.notifiedArticleIds.includes(article.id);
                if (!hasBeenNotified && checkMatch(article, sub)) {
                    // Match gefunden & noch nicht benachrichtigt!
                    await sendNotificationEmail(sub.email, article);
                    sub.notifiedArticleIds.push(article.id); // Markiere als benachrichtigt
                }
            }
        }
        // ENDE: E-MAIL-LOGIK

        await db.write(); // Speichere alle Änderungen (Tags UND 'notifiedArticleIds')
        
        res.status(200).json({ updatedArticles: articles, allTags: tags });
    } catch (error) {
        console.error("Error processing tag:", error);
        res.status(500).json({ message: "Server error while processing tag." });
    }
});

// --- SERVER START ---
app.listen(PORT, () => {
  console.log(`Backend server is running on http://localhost:${3001}`);
});