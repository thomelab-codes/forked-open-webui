<script lang="ts">
	import { toast } from 'svelte-sonner';
	import { onMount, getContext } from 'svelte';
	import { goto } from '$app/navigation';

	import { user } from '$lib/stores';
	import { videoGenerations } from '$lib/apis/videos';

	import Spinner from '$lib/components/common/Spinner.svelte';

	const i18n = getContext('i18n');

	let loaded = false;
	let loading = false;

	let prompt = '';
	let generatedVideos: { url: string }[] = [];

	let promptTextareaElement: HTMLTextAreaElement;

	const resizePromptTextarea = () => {
		if (promptTextareaElement) {
			promptTextareaElement.style.height = '';
			promptTextareaElement.style.height = Math.min(promptTextareaElement.scrollHeight, 150) + 'px';
		}
	};

	const submitHandler = async () => {
		if (!prompt.trim()) {
			toast.error($i18n.t('Please enter a prompt'));
			return;
		}

		loading = true;
		try {
			const result = await videoGenerations(localStorage.token, prompt);

			if (result) {
				generatedVideos = [...result, ...generatedVideos];
			}
		} catch (error) {
			console.error('Video generation error:', error);
			toast.error(`${error}`);
		} finally {
			loading = false;
		}
	};

	const downloadVideo = async (url: string, index: number) => {
		try {
			const response = await fetch(url);
			const blob = await response.blob();
			const blobUrl = URL.createObjectURL(blob);
			const a = document.createElement('a');
			a.href = blobUrl;
			a.download = `video-${Date.now()}-${index}.mp4`;
			a.click();
			URL.revokeObjectURL(blobUrl);
		} catch (error) {
			toast.error($i18n.t('Failed to download video'));
		}
	};

	onMount(async () => {
		if ($user?.role !== 'admin') {
			await goto('/');
			return;
		}
		loaded = true;
	});
</script>

<div class=" flex flex-col justify-between w-full overflow-y-auto h-full">
	<div class="mx-auto w-full md:px-0 h-full">
		<div class=" flex flex-col h-full px-4">
			<!-- Results Area -->
			<div
				class=" pt-0.5 pb-2.5 flex flex-col justify-between w-full flex-auto overflow-auto h-0"
				id="videos-container"
			>
				<div class=" h-full w-full flex flex-col">
					<div class="flex-1 p-1">
						{#if generatedVideos.length > 0}
							<div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
								{#each generatedVideos as video, index}
									<div class="relative group">
										<!-- svelte-ignore a11y-media-has-caption -->
										<video
											src={video.url}
											class="w-full rounded-lg border border-gray-100/30 dark:border-gray-850/30"
											controls
											preload="metadata"
										/>
										<div class="mt-1 flex justify-end">
											<button
												class="px-2 py-1 text-xs font-medium bg-gray-50 hover:bg-gray-100 text-gray-700 dark:bg-gray-850 dark:hover:bg-gray-800 dark:text-gray-300 transition rounded-md"
												on:click={() => downloadVideo(video.url, index)}
											>
												{$i18n.t('Download')}
											</button>
										</div>
									</div>
								{/each}
							</div>
						{:else}
							<div
								class="h-full flex items-center justify-center text-gray-400 dark:text-gray-600 text-sm"
							>
								{$i18n.t('Generated videos will appear here')}
							</div>
						{/if}
					</div>
				</div>
			</div>

			<!-- Input Area -->
			<div class="pb-3">
				<div
					class="border border-gray-100/30 dark:border-gray-850/30 w-full px-3 py-2.5 rounded-xl"
				>
					<!-- Prompt Textarea -->
					<div class="py-0.5">
						<textarea
							bind:this={promptTextareaElement}
							bind:value={prompt}
							class=" w-full h-full bg-transparent resize-none outline-hidden text-sm"
							placeholder={$i18n.t('Describe the video...')}
							on:input={resizePromptTextarea}
							on:focus={resizePromptTextarea}
							on:keydown={(e) => {
								if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && !loading) {
									e.preventDefault();
									submitHandler();
								}
							}}
							rows="2"
						/>
					</div>

					<!-- Actions -->
					<div class="flex justify-end items-center gap-2 mt-2">
						<div class="flex gap-2 shrink-0">
							{#if !loading}
								<button
									disabled={prompt.trim() === ''}
									class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
									on:click={submitHandler}
								>
									{$i18n.t('Run')}
								</button>
							{:else}
								<button
									class="px-3.5 py-1.5 text-sm font-medium bg-gray-300 text-black transition rounded-lg flex items-center gap-2"
									disabled
								>
									<Spinner className="size-4" />
									{$i18n.t('Generating...')}
								</button>
							{/if}
						</div>
					</div>
				</div>
			</div>
		</div>
	</div>
</div>
