import { RuntimeClient, HTTPResponseHelper, SSEParser } from '../../../sdk-typescript/dist';

async function main() {
    const client = new RuntimeClient({ tenantId: 'gemini-connector' });
    try {
        await client.connect();
        console.log("🚀 Gemini Connector Active via Vastar Runtime...");

        const response = await client.executeHTTP({
            method: 'POST',
            url: https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:streamGenerateContent?alt=sse,
            headers: {
                'Content-Type': 'application/json',
                'x-goog-api-key': process.env.GEMINI_API_KEY! // Ubah menjadi GEMINI_API_KEY
        },
            body: JSON.stringify({
                contents: [{ parts: [{ text: "apa itu unsika?" }] }]
            })
        });

        // ... kode sebelumnya ...
        if (HTTPResponseHelper.is2xx(response)) {
        const sseData = HTTPResponseHelper.getBodyAsString(response);
        
        // Kita akan mengekstrak teks dari format JSON Gemini: candidates[0].content.parts[0].text
        // SSE Gemini biasanya mengirimkan banyak baris 'data: {...}'
        const lines = sseData.split('\n');
        let fullText = "";

        for (const line of lines) {
            if (line.startsWith('data: ')) {
                try {
                    const jsonStr = line.replace('data: ', '');
                    const data = JSON.parse(jsonStr);
                    // Navigasi ke struktur teks Gemini
                    const content = data.candidates?.[0]?.content?.parts?.[0]?.text;
                    if (content) fullText += content;
                } catch (e) {
                    // Abaikan jika baris bukan JSON yang valid (seperti baris kosong)
                }
            }
        }

        console.log("\n🤖 Jawaban Gemini:");
        console.log(fullText || "Gemini terhubung tapi tidak mengirim teks. Periksa API Key Anda.");
    }
// ... kode close ...
    } catch (e) {
        console.error("❌ Error:", e);
    } finally {
        await client.close();
    }
}
main();