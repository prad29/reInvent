import { WEBUI_API_BASE_URL } from '$lib/constants';

export interface Language {
	code: string;
	name: string;
}

export interface LanguagesResponse {
	languages: Language[];
}

export interface DetectLanguageResponse {
	language: string;
	confidence: number;
}

export interface TranslateResponse {
	translatedText: string;
	detectedLanguage?: string;
}

export interface FileUploadResponse {
	fileId: string;
	filename: string;
	size: number;
	extractedText: string;
	fileExtension: string;
}

export interface TranslateFileResponse {
	translatedText?: string; // For TXT/PDF (text-only formats)
	translatedFileId?: string; // For DOCX (format-preserving)
	detectedLanguage?: string;
	filename: string;
	preservedFormat: boolean; // True if format was preserved (DOCX)
}

/**
 * Get available languages from LibreTranslate
 */
export const getLanguages = async (token: string): Promise<LanguagesResponse> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/translation/languages`, {
		method: 'GET',
		headers: {
			Accept: 'application/json',
			authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		const error = await res.json();
		throw new Error(error.detail || 'Failed to fetch languages');
	}

	return res.json();
};

/**
 * Auto-detect language of text
 */
export const detectLanguage = async (
	token: string,
	text: string
): Promise<DetectLanguageResponse> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/translation/detect`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ text })
	});

	if (!res.ok) {
		const error = await res.json();
		throw new Error(error.detail || 'Failed to detect language');
	}

	return res.json();
};

/**
 * Translate text from source to target language
 */
export const translateText = async (
	token: string,
	text: string,
	source: string,
	target: string
): Promise<TranslateResponse> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/translation/translate`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ text, source, target })
	});

	if (!res.ok) {
		const error = await res.json();
		throw new Error(error.detail || 'Translation failed');
	}

	return res.json();
};

/**
 * Upload file for translation
 */
export const uploadFile = async (token: string, file: File): Promise<FileUploadResponse> => {
	const formData = new FormData();
	formData.append('file', file);

	const res = await fetch(`${WEBUI_API_BASE_URL}/translation/file/upload`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			authorization: `Bearer ${token}`
		},
		body: formData
	});

	if (!res.ok) {
		const error = await res.json();
		throw new Error(error.detail || 'File upload failed');
	}

	return res.json();
};

/**
 * Translate an uploaded file
 */
export const translateFile = async (
	token: string,
	fileId: string,
	source: string,
	target: string
): Promise<TranslateFileResponse> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/translation/file/translate`, {
		method: 'POST',
		headers: {
			Accept: 'application/json',
			'Content-Type': 'application/json',
			authorization: `Bearer ${token}`
		},
		body: JSON.stringify({ fileId, source, target })
	});

	if (!res.ok) {
		const error = await res.json();
		throw new Error(error.detail || 'File translation failed');
	}

	return res.json();
};

/**
 * Download translated DOCX file
 */
export const downloadTranslatedFile = async (token: string, fileId: string, filename: string): Promise<void> => {
	const res = await fetch(`${WEBUI_API_BASE_URL}/translation/file/download/${fileId}`, {
		method: 'GET',
		headers: {
			authorization: `Bearer ${token}`
		}
	});

	if (!res.ok) {
		const error = await res.json().catch(() => ({ detail: 'File download failed' }));
		throw new Error(error.detail || 'File download failed');
	}

	const blob = await res.blob();
	const url = window.URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.style.display = 'none';
	a.href = url;
	a.download = filename;
	document.body.appendChild(a);
	a.click();
	window.URL.revokeObjectURL(url);
	document.body.removeChild(a);
};

/**
 * Helper to trigger text file download in browser
 */
export const downloadTextAsFile = (text: string, filename: string, mimeType: string = 'text/plain') => {
	const blob = new Blob([text], { type: mimeType });
	const url = window.URL.createObjectURL(blob);
	const a = document.createElement('a');
	a.style.display = 'none';
	a.href = url;
	a.download = filename;
	document.body.appendChild(a);
	a.click();
	window.URL.revokeObjectURL(url);
	document.body.removeChild(a);
};
