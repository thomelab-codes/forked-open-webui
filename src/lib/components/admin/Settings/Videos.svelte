<script lang="ts">
	import { toast } from 'svelte-sonner';

	import { createEventDispatcher, onMount, getContext } from 'svelte';
	import { config as backendConfig, user } from '$lib/stores';

	import { getBackendConfig } from '$lib/apis';
	import {
		getVideoGenerationModels,
		getConfig,
		updateConfig
	} from '$lib/apis/videos';
	import SensitiveInput from '$lib/components/common/SensitiveInput.svelte';
	import Switch from '$lib/components/common/Switch.svelte';
	import Tooltip from '$lib/components/common/Tooltip.svelte';
	const dispatch = createEventDispatcher();

	const i18n = getContext('i18n');

	let loading = false;

	let models = null;
	let config = null;

	const getModels = async () => {
		models = await getVideoGenerationModels(localStorage.token).catch((error) => {
			toast.error(`${error}`);
			return null;
		});
	};

	const updateConfigHandler = async () => {
		if (config.VIDEO_GENERATION_ENGINE === 'openai' && config.VIDEOS_OPENAI_API_KEY === '') {
			toast.error($i18n.t('OpenAI API Key is required.'));
			config.ENABLE_VIDEO_GENERATION = false;
			return null;
		} else if (
			config.VIDEO_GENERATION_ENGINE === 'gemini' &&
			config.VIDEOS_GEMINI_API_KEY === ''
		) {
			toast.error($i18n.t('Gemini API Key is required.'));
			config.ENABLE_VIDEO_GENERATION = false;
			return null;
		}

		const res = await updateConfig(localStorage.token, config).catch((error) => {
			toast.error(`${error}`);
			return null;
		});

		if (res) {
			if (res.ENABLE_VIDEO_GENERATION) {
				backendConfig.set(await getBackendConfig());
				getModels();
			}

			return res;
		}

		return null;
	};

	const saveHandler = async () => {
		loading = true;

		const res = await updateConfigHandler();
		if (res) {
			dispatch('save');
		}

		loading = false;
	};

	onMount(async () => {
		if ($user?.role === 'admin') {
			const res = await getConfig(localStorage.token).catch((error) => {
				toast.error(`${error}`);
				return null;
			});

			if (res) {
				config = res;
			}

			if (config.ENABLE_VIDEO_GENERATION) {
				getModels();
			}
		}
	});
</script>

<form
	class="flex flex-col h-full justify-between space-y-3 text-sm"
	on:submit|preventDefault={async () => {
		saveHandler();
	}}
>
	<div class=" space-y-3 overflow-y-scroll scrollbar-hidden pr-2">
		{#if config}
			<div>
				<div class="mb-3">
					<div class=" mt-0.5 mb-2.5 text-base font-medium">{$i18n.t('General')}</div>

					<hr class=" border-gray-100/30 dark:border-gray-850/30 my-2" />

					<div class="mb-2.5">
						<div class="flex w-full justify-between items-center">
							<div class="text-xs pr-2">
								<div class="">
									{$i18n.t('Video Generation')}
								</div>
							</div>

							<Switch bind:state={config.ENABLE_VIDEO_GENERATION} />
						</div>
					</div>
				</div>

				<div class="mb-3">
					<div class=" mt-0.5 mb-2.5 text-base font-medium">{$i18n.t('Generate Video')}</div>

					<hr class=" border-gray-100/30 dark:border-gray-850/30 my-2" />

					{#if config.ENABLE_VIDEO_GENERATION}
						<div class="mb-2.5">
							<div class="flex w-full justify-between items-center">
								<div class="text-xs pr-2">
									<div class="shrink-0">
										{$i18n.t('Model')}
									</div>
								</div>

								<Tooltip content={$i18n.t('Enter Model ID')} placement="top-start">
									<input
										list="video-model-list"
										class=" text-right text-sm bg-transparent outline-hidden max-w-full w-52"
										bind:value={config.VIDEO_GENERATION_MODEL}
										placeholder={$i18n.t('Select a model')}
										required
									/>

									<datalist id="video-model-list">
										{#each models ?? [] as model}
											<option value={model.id}>{model.name}</option>
										{/each}
									</datalist>
								</Tooltip>
							</div>
						</div>
					{/if}

					<div class="mb-2.5">
						<div class="flex w-full justify-between items-center">
							<div class="text-xs pr-2">
								<div class="">
									{$i18n.t('Video Generation Engine')}
								</div>
							</div>

							<select
								class=" dark:bg-gray-900 w-fit pr-8 cursor-pointer rounded-sm px-2 text-xs bg-transparent outline-hidden text-right"
								bind:value={config.VIDEO_GENERATION_ENGINE}
								placeholder={$i18n.t('Select Engine')}
							>
								<option value="openai">{$i18n.t('OpenAI')}</option>
								<option value="gemini">{$i18n.t('Google Gemini')}</option>
							</select>
						</div>
					</div>

					{#if config?.VIDEO_GENERATION_ENGINE === 'openai'}
						<div class="mb-2.5">
							<div class="flex w-full justify-between items-center">
								<div class="text-xs pr-2 shrink-0">
									<div class="">
										{$i18n.t('OpenAI API Base URL')}
									</div>
								</div>

								<div class="flex w-full">
									<div class="flex-1">
										<input
											class="w-full text-sm bg-transparent outline-hidden text-right"
											placeholder={$i18n.t('API Base URL')}
											bind:value={config.VIDEOS_OPENAI_API_BASE_URL}
										/>
									</div>
								</div>
							</div>
						</div>

						<div class="mb-2.5">
							<div class="flex w-full justify-between items-center">
								<div class="text-xs pr-2 shrink-0">
									<div class="">
										{$i18n.t('OpenAI API Key')}
									</div>
								</div>

								<div class="flex w-full">
									<div class="flex-1">
										<SensitiveInput
											inputClassName="text-right w-full"
											placeholder={$i18n.t('API Key')}
											bind:value={config.VIDEOS_OPENAI_API_KEY}
											required={false}
										/>
									</div>
								</div>
							</div>
						</div>
					{:else if config?.VIDEO_GENERATION_ENGINE === 'gemini'}
						<div class="mb-2.5">
							<div class="flex w-full justify-between items-center">
								<div class="text-xs pr-2 shrink-0">
									<div class="">
										{$i18n.t('Gemini API Base URL')}
									</div>
								</div>

								<div class="flex w-full">
									<div class="flex-1">
										<input
											class="w-full text-sm bg-transparent outline-hidden text-right"
											placeholder={$i18n.t('API Base URL')}
											bind:value={config.VIDEOS_GEMINI_API_BASE_URL}
										/>
									</div>
								</div>
							</div>
						</div>

						<div class="mb-2.5">
							<div class="flex w-full justify-between items-center">
								<div class="text-xs pr-2 shrink-0">
									<div class="">
										{$i18n.t('Gemini API Key')}
									</div>
								</div>

								<div class="flex w-full">
									<div class="flex-1">
										<SensitiveInput
											inputClassName="text-right w-full"
											placeholder={$i18n.t('API Key')}
											bind:value={config.VIDEOS_GEMINI_API_KEY}
											required={false}
										/>
									</div>
								</div>
							</div>
						</div>
					{/if}
				</div>
			</div>
		{/if}
	</div>
	<div class="flex justify-end pt-3">
		<button
			class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-lg disabled:cursor-not-allowed disabled:opacity-50"
			type="submit"
			disabled={loading}
		>
			{$i18n.t('Save')}
		</button>
	</div>
</form>
