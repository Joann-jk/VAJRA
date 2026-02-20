import React, { useState } from 'react';
import { analyzeFile } from '../services/api';

/*
  UploadForm
  - Lets the user choose input_type (text or audio), pick a file, and submit
  - Uses FormData to send multipart/form-data to the backend
*/
export default function UploadForm({ onStart, onResult, onError }) {
  const [inputType, setInputType] = useState('text');
  const [file, setFile] = useState(null);

  async function handleSubmit(e) {
    e.preventDefault();
    if (!file) {
      onError && onError('Please choose a file to upload');
      return;
    }

    onStart && onStart();

    const formData = new FormData();
    formData.append('input_type', inputType);
    formData.append('file', file, file.name);

    try {
      const res = await analyzeFile(formData);
      if (res.error) {
        onError && onError(res.error);
      } else {
        onResult && onResult(res);
      }
    } catch (err) {
      onError && onError(err.message || 'Unknown error');
    }
  }

  return (
    <form className="upload-form" onSubmit={handleSubmit}>
      <label>
        Input type
        <select value={inputType} onChange={(e) => setInputType(e.target.value)}>
          <option value="text">text</option>
          <option value="audio">audio</option>
        </select>
      </label>

      <label>
        File
        <input
          type="file"
          onChange={(e) => setFile(e.target.files && e.target.files[0])}
        />
      </label>

      <div>
        <button type="submit" className="btn">Analyze</button>
      </div>
    </form>
  );
}
