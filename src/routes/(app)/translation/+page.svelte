<script lang="ts">
	import { onMount, getContext } from 'svelte';
	import { user, showSidebar, mobile } from '$lib/stores';
	import { toast } from 'svelte-sonner';
	import {
		getLanguages,
		translateText,
		uploadFile,
		translateFile,
		downloadTextAsFile,
		downloadTranslatedFile,
		type Language
	} from '$lib/apis/translation';

	const i18n = getContext('i18n');

	// State
	let sourceText = '';
	let translatedText = '';
	let sourceLang = 'auto';
	let targetLang = 'de';
	let languages: Language[] = [];
	let realtimeEnabled = false;
	let isTranslating = false;
	let uploadedFileId: string | null = null;
	let uploadedFileName: string = '';
	let uploadedFileSize: number = 0;
	let uploadedFileExtension: string = '';
	let translatedFileId: string | null = null;
	let preservedFormat: boolean = false;
	let hasTranslatedFile: boolean = false;

	let debounceTimer: NodeJS.Timeout;
	const DEBOUNCE_DELAY = 800;

	// File input reference
	let fileInput: HTMLInputElement;
	let isDragging = false;

	// Character and word count
	$: sourceStats = countStats(sourceText);
	$: targetStats = countStats(translatedText);

	onMount(async () => {
		await loadLanguages();
	});

	/**
	 * Load available languages from API
	 */
	const loadLanguages = async () => {
		try {
			const response = await getLanguages($user.token);
			languages = response.languages;
		} catch (error) {
			console.error('Failed to load languages:', error);
			toast.error(
				$i18n.t('Translation service unavailable. Please ensure LibreTranslate is running.')
			);
		}
	};

	/**
	 * Count characters and words in text
	 */
	const countStats = (text: string) => {
		const chars = text.length;
		const words = text.trim().split(/\s+/).filter((w) => w.length > 0).length;
		return { chars, words };
	};

	/**
	 * Handle source text change for real-time translation
	 */
	const handleSourceTextChange = () => {
		if (!realtimeEnabled || !sourceText.trim()) {
			return;
		}

		clearTimeout(debounceTimer);
		debounceTimer = setTimeout(() => {
			handleTranslate();
		}, DEBOUNCE_DELAY);
	};

	/**
	 * Translate text
	 */
	const handleTranslate = async () => {
		if (!sourceText.trim()) {
			toast.error($i18n.t('Please enter text to translate'));
			return;
		}

		if (!targetLang) {
			toast.error($i18n.t('Please select a target language'));
			return;
		}

		isTranslating = true;

		try {
			const response = await translateText($user.token, sourceText, sourceLang, targetLang);
			translatedText = response.translatedText;

			if (response.detectedLanguage && sourceLang === 'auto') {
				// Update detected language
				const detectedLang = languages.find((l) => l.code === response.detectedLanguage);
				if (detectedLang) {
					toast.success($i18n.t(`Detected language: ${detectedLang.name}`));
				}
			}

			if (!realtimeEnabled) {
				toast.success($i18n.t('Translation complete'));
			}
		} catch (error) {
			console.error('Translation error:', error);
			toast.error($i18n.t(error.message || 'Translation failed'));
		} finally {
			isTranslating = false;
		}
	};

	/**
	 * Swap source and target languages
	 */
	const handleSwapLanguages = () => {
		if (sourceLang === 'auto') {
			toast.error($i18n.t('Cannot swap when source is auto-detect'));
			return;
		}

		// Swap languages
		[sourceLang, targetLang] = [targetLang, sourceLang];

		// Swap text
		[sourceText, translatedText] = [translatedText, sourceText];

		toast.success($i18n.t('Languages swapped'));
	};

	/**
	 * Copy translated text to clipboard
	 */
	const handleCopyToClipboard = async () => {
		if (!translatedText) {
			toast.error($i18n.t('No translation to copy'));
			return;
		}

		try {
			await navigator.clipboard.writeText(translatedText);
			toast.success($i18n.t('Copied to clipboard'));
		} catch (error) {
			console.error('Copy error:', error);
			toast.error($i18n.t('Failed to copy to clipboard'));
		}
	};

	/**
	 * Handle file upload (drag-and-drop or click)
	 */
	const handleFileUpload = async (file: File) => {
		// Validate file type
		const allowedExtensions = ['.pdf', '.txt', '.doc', '.docx'];
		const fileExt = '.' + file.name.split('.').pop()?.toLowerCase();

		if (!allowedExtensions.includes(fileExt)) {
			toast.error(
				$i18n.t(`Unsupported file type. Allowed types: ${allowedExtensions.join(', ')}`)
			);
			return;
		}

		// Validate file size (5MB)
		const maxSize = 5 * 1024 * 1024;
		if (file.size > maxSize) {
			toast.error($i18n.t('File size exceeds 5MB'));
			return;
		}

		if (file.size === 0) {
			toast.error($i18n.t('File is empty'));
			return;
		}

		try {
			isTranslating = true;
			toast.info($i18n.t('Uploading file...'));

			// Upload file
			const uploadResponse = await uploadFile($user.token, file);
			uploadedFileId = uploadResponse.fileId;
			uploadedFileName = uploadResponse.filename;
			uploadedFileSize = uploadResponse.size;
			uploadedFileExtension = uploadResponse.fileExtension;

			// Display extracted text in source column
			sourceText = uploadResponse.extractedText;

			toast.success($i18n.t('File uploaded successfully'));

			// Translate file
			toast.info($i18n.t('Translating file...'));
			const translateResponse = await translateFile(
				$user.token,
				uploadedFileId,
				sourceLang,
				targetLang
			);

			// Handle response based on format preservation
			preservedFormat = translateResponse.preservedFormat;

			if (preservedFormat && translateResponse.translatedFileId) {
				// DOCX: Format preserved, file available for download
				translatedFileId = translateResponse.translatedFileId;
				translatedText = ''; // Clear text area for DOCX
				hasTranslatedFile = true;
				toast.success($i18n.t('File translated successfully - Download to view'));
			} else if (translateResponse.translatedText) {
				// TXT/PDF: Display translated text
				translatedText = translateResponse.translatedText;
				translatedFileId = null;
				hasTranslatedFile = true;
				toast.success($i18n.t('File translated successfully'));
			}
		} catch (error) {
			console.error('File upload/translation error:', error);
			toast.error($i18n.t(error.message || 'File translation failed'));
			// Clear file state on error
			uploadedFileId = null;
			uploadedFileName = '';
			uploadedFileSize = 0;
			uploadedFileExtension = '';
			translatedFileId = null;
			preservedFormat = false;
			hasTranslatedFile = false;
		} finally {
			isTranslating = false;
		}
	};

	/**
	 * Handle file input change
	 */
	const onFileInputChange = (event: Event) => {
		const target = event.target as HTMLInputElement;
		const file = target.files?.[0];
		if (file) {
			handleFileUpload(file);
		}
		// Reset input
		target.value = '';
	};

	/**
	 * Handle drag and drop
	 */
	const onDragOver = (event: DragEvent) => {
		event.preventDefault();
		isDragging = true;
	};

	const onDragLeave = (event: DragEvent) => {
		event.preventDefault();
		isDragging = false;
	};

	const onDrop = (event: DragEvent) => {
		event.preventDefault();
		isDragging = false;

		const file = event.dataTransfer?.files?.[0];
		if (file) {
			handleFileUpload(file);
		}
	};

	/**
	 * Download translated file (DOCX with format preservation or TXT)
	 */
	const handleDownloadFile = async () => {
		if (!hasTranslatedFile) {
			toast.error($i18n.t('No translated file available'));
			return;
		}

		try {
			// DOCX: Download from server with format preservation
			if (preservedFormat && translatedFileId) {
				toast.info($i18n.t('Downloading file...'));
				const filename = uploadedFileName
					? `translated_${uploadedFileName}`
					: 'translated.docx';
				await downloadTranslatedFile($user.token, translatedFileId, filename);
				toast.success($i18n.t('File downloaded successfully'));
			}
			// TXT/PDF: Download as text file
			else if (translatedText) {
				const filename = uploadedFileName
					? `translated_${uploadedFileName.replace(/\.[^/.]+$/, '')}.txt`
					: 'translated.txt';
				downloadTextAsFile(translatedText, filename, 'text/plain');
				toast.success($i18n.t('File downloaded successfully'));
			} else {
				toast.error($i18n.t('No translated file available'));
			}
		} catch (error) {
			console.error('Download error:', error);
			toast.error($i18n.t('File download failed'));
		}
	};

	/**
	 * Clear all content
	 */
	const handleClear = () => {
		sourceText = '';
		translatedText = '';
		uploadedFileId = null;
		uploadedFileName = '';
		uploadedFileSize = 0;
		uploadedFileExtension = '';
		translatedFileId = null;
		preservedFormat = false;
		hasTranslatedFile = false;
	};
</script>

<div
	class="h-screen max-h-[100dvh] transition-width duration-200 ease-in-out {$showSidebar
		? 'md:max-w-[calc(100%-260px)]'
		: ''} w-full max-w-full flex flex-col"
>
	<!-- Navbar -->
	<div
		class="sticky top-0 z-10 flex justify-between items-center px-4 py-3 bg-white dark:bg-gray-900 border-b dark:border-gray-800"
	>
		<div class="flex items-center gap-2">
			{#if $mobile}
				<button
					class="text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 p-2 rounded-xl"
					on:click={() => {
						showSidebar.set(!$showSidebar);
					}}
				>
					<svg
						xmlns="http://www.w3.org/2000/svg"
						fill="none"
						viewBox="0 0 24 24"
						stroke-width="1.5"
						stroke="currentColor"
						class="w-6 h-6"
					>
						<path
							stroke-linecap="round"
							stroke-linejoin="round"
							d="M3.75 6.75h16.5M3.75 12h16.5m-16.5 5.25h16.5"
						/>
					</svg>
				</button>
			{/if}
			<div class="text-xl font-semibold dark:text-white">
				{$i18n.t('Translation')}
			</div>
		</div>

		<button
			class="text-gray-600 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800 px-3 py-2 rounded-xl text-sm"
			on:click={handleClear}
		>
			{$i18n.t('Clear')}
		</button>
	</div>

	<!-- Main Content -->
	<div class="flex-1 overflow-hidden">
		<div class="h-full p-4 md:p-6">
			<!-- Control Bar -->
			<div
				class="mb-4 flex flex-col md:flex-row items-start md:items-center gap-4 p-4 bg-gray-50 dark:bg-gray-850 rounded-xl"
			>
				<!-- Language Selectors -->
				<div class="flex items-center gap-2 flex-wrap">
					<!-- Source Language -->
					<select
						bind:value={sourceLang}
						class="px-3 py-2 rounded-xl border dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
					>
						<option value="auto">{$i18n.t('Auto-detect')}</option>
						{#each languages as lang}
							<option value={lang.code}>{lang.name}</option>
						{/each}
					</select>

					<!-- Swap Button -->
					<button
						class="p-2 hover:bg-gray-200 dark:hover:bg-gray-700 rounded-xl transition"
						on:click={handleSwapLanguages}
						disabled={sourceLang === 'auto'}
						title={$i18n.t('Swap Languages')}
					>
						<svg
							xmlns="http://www.w3.org/2000/svg"
							fill="none"
							viewBox="0 0 24 24"
							stroke-width="1.5"
							stroke="currentColor"
							class="w-5 h-5"
						>
							<path
								stroke-linecap="round"
								stroke-linejoin="round"
								d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5"
							/>
						</svg>
					</button>

					<!-- Target Language -->
					<select
						bind:value={targetLang}
						class="px-3 py-2 rounded-xl border dark:border-gray-700 bg-white dark:bg-gray-800 text-sm"
					>
						{#each languages as lang}
							<option value={lang.code}>{lang.name}</option>
						{/each}
					</select>
				</div>

				<!-- Translation Controls -->
				<div class="flex items-center gap-4 ml-auto">
					<!-- Real-time Toggle -->
					<label class="flex items-center gap-2 cursor-pointer">
						<input type="checkbox" bind:checked={realtimeEnabled} class="rounded" />
						<span class="text-sm dark:text-gray-300">{$i18n.t('Real-time')}</span>
					</label>

					<!-- Translate Button -->
					<button
						class="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-sm font-medium transition disabled:opacity-50"
						on:click={handleTranslate}
						disabled={isTranslating || !sourceText.trim()}
					>
						{isTranslating ? $i18n.t('Translating...') : $i18n.t('Translate')}
					</button>
				</div>
			</div>

			<!-- Two-Column Layout -->
			<div class="h-[calc(100%-5rem)] grid grid-cols-1 md:grid-cols-2 gap-4">
				<!-- Source Column -->
				<div class="flex flex-col h-full">
					<div class="flex-1 relative">
						<textarea
							bind:value={sourceText}
							on:input={handleSourceTextChange}
							class="w-full h-full p-4 rounded-xl border dark:border-gray-700 bg-white dark:bg-gray-800 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
							placeholder={$i18n.t('Enter text or drag and drop a file here...')}
							on:dragover={onDragOver}
							on:dragleave={onDragLeave}
							on:drop={onDrop}
						/>

						<!-- Drag overlay -->
						{#if isDragging}
							<div
								class="absolute inset-0 bg-blue-500 bg-opacity-10 border-2 border-dashed border-blue-500 rounded-xl flex items-center justify-center pointer-events-none"
							>
								<div class="text-blue-600 dark:text-blue-400 text-lg font-medium">
									{$i18n.t('Drop file here')}
								</div>
							</div>
						{/if}
					</div>

					<!-- Source Controls -->
					<div class="mt-2 flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
						<div>
							{sourceStats.chars}
							{$i18n.t('characters')} • {sourceStats.words}
							{$i18n.t('words')}
						</div>
						<button
							class="px-3 py-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg"
							on:click={() => fileInput.click()}
						>
							{$i18n.t('Upload File')}
						</button>
					</div>

					<!-- Uploaded File Indicator -->
					{#if uploadedFileId && uploadedFileName}
						<div class="mt-2 p-3 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
							<div class="flex items-center gap-2">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-5 h-5 text-green-600 dark:text-green-400"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
									/>
								</svg>
								<div class="flex-1 min-w-0">
									<div class="text-sm font-medium text-green-700 dark:text-green-300 truncate">
										{uploadedFileName}
									</div>
									<div class="text-xs text-green-600 dark:text-green-400">
										{(uploadedFileSize / 1024).toFixed(1)} KB • Uploaded
									</div>
								</div>
							</div>
						</div>
					{/if}

					<!-- Hidden file input -->
					<input
						type="file"
						bind:this={fileInput}
						on:change={onFileInputChange}
						accept=".pdf,.txt,.doc,.docx"
						class="hidden"
					/>
				</div>

				<!-- Target Column -->
				<div class="flex flex-col h-full">
					<div class="flex-1">
						<textarea
							bind:value={translatedText}
							class="w-full h-full p-4 rounded-xl border dark:border-gray-700 bg-white dark:bg-gray-800 resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
							placeholder={$i18n.t('Translation will appear here...')}
						/>
					</div>

					<!-- Target Controls -->
					<div class="mt-2 flex items-center justify-between text-sm text-gray-600 dark:text-gray-400">
						<div>
							{targetStats.chars}
							{$i18n.t('characters')} • {targetStats.words}
							{$i18n.t('words')}
						</div>
						<div class="flex gap-2">
							<!-- Copy Button -->
							<button
								class="px-3 py-1 hover:bg-gray-100 dark:hover:bg-gray-800 rounded-lg flex items-center gap-1"
								on:click={handleCopyToClipboard}
								disabled={!translatedText}
							>
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-4 h-4"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M15.666 3.888A2.25 2.25 0 0013.5 2.25h-3c-1.03 0-1.9.693-2.166 1.638m7.332 0c.055.194.084.4.084.612v0a.75.75 0 01-.75.75H9a.75.75 0 01-.75-.75v0c0-.212.03-.418.084-.612m7.332 0c.646.049 1.288.11 1.927.184 1.1.128 1.907 1.077 1.907 2.185V19.5a2.25 2.25 0 01-2.25 2.25H6.75A2.25 2.25 0 014.5 19.5V6.257c0-1.108.806-2.057 1.907-2.185a48.208 48.208 0 011.927-.184"
									/>
								</svg>
								{$i18n.t('Copy')}
							</button>

							<!-- Download Button (if file was translated) -->
							{#if hasTranslatedFile}
								<button
									class="px-3 py-1 bg-blue-600 hover:bg-blue-700 text-white rounded-lg flex items-center gap-1"
									on:click={handleDownloadFile}
								>
									<svg
										xmlns="http://www.w3.org/2000/svg"
										fill="none"
										viewBox="0 0 24 24"
										stroke-width="1.5"
										stroke="currentColor"
										class="w-4 h-4"
									>
										<path
											stroke-linecap="round"
											stroke-linejoin="round"
											d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12m4.5 4.5V3"
										/>
									</svg>
									{$i18n.t('Download')}
								</button>
							{/if}
						</div>
					</div>

					<!-- Translated File Ready Indicator -->
					{#if hasTranslatedFile && uploadedFileName}
						<div class="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
							<div class="flex items-center gap-2">
								<svg
									xmlns="http://www.w3.org/2000/svg"
									fill="none"
									viewBox="0 0 24 24"
									stroke-width="1.5"
									stroke="currentColor"
									class="w-5 h-5 text-blue-600 dark:text-blue-400"
								>
									<path
										stroke-linecap="round"
										stroke-linejoin="round"
										d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
									/>
								</svg>
								<div class="flex-1 min-w-0">
									<div class="text-sm font-medium text-blue-700 dark:text-blue-300 truncate">
										{#if preservedFormat}
											translated_{uploadedFileName}
										{:else}
											translated_{uploadedFileName.replace(/\.[^/.]+$/, '')}.txt
										{/if}
									</div>
									<div class="text-xs text-blue-600 dark:text-blue-400">
										{#if preservedFormat}
											Format preserved • Ready for download
										{:else}
											Ready for download
										{/if}
									</div>
								</div>
							</div>
						</div>
					{/if}
				</div>
			</div>
		</div>
	</div>
</div>
