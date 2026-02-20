// api.js
// Small wrapper to call the backend /analyze endpoint with multipart/form-data

export async function analyzeFile(formData) {
  try {
    const res = await fetch('http://localhost:8000/analyze', {
      method: 'POST',
      body: formData,
    });

    if (!res.ok) {
      const text = await res.text();
      return { error: `Server returned status ${res.status}: ${text}` };
    }

    const data = await res.json();
    return data;
  } catch (err) {
    return { error: err.message || 'Network error' };
  }
}
