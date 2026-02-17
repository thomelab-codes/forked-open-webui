<script lang="ts">
import Switch from '$lib/components/common/Switch.svelte';
import { config, models, settings, user } from '$lib/stores';
import { createEventDispatcher, onMount, getContext, tick } from 'svelte';
import { toast } from 'svelte-sonner';
import ManageModal from './Personalization/ManageModal.svelte';
import Tooltip from '$lib/components/common/Tooltip.svelte';
const dispatch = createEventDispatcher();

const i18n = getContext('i18n');

export let saveSettings: Function;

let showManageModal = false;

// Addons
let enableMemory = false;

// Custom Instructions
let customInstructions = '';

// Response Preferences
let responseTone = 'default';
let responseVerbosity = 'default';
let responseFormat = 'default';

// User Profile Context
let userProfileAbout = '';

onMount(async () => {
enableMemory = $settings?.memory ?? false;
customInstructions = $settings?.customInstructions ?? '';
responseTone = $settings?.responseTone ?? 'default';
responseVerbosity = $settings?.responseVerbosity ?? 'default';
responseFormat = $settings?.responseFormat ?? 'default';
userProfileAbout = $settings?.userProfileAbout ?? '';
});

const saveHandler = async () => {
saveSettings({
memory: enableMemory,
customInstructions: customInstructions !== '' ? customInstructions : undefined,
responseTone: responseTone !== 'default' ? responseTone : undefined,
responseVerbosity: responseVerbosity !== 'default' ? responseVerbosity : undefined,
responseFormat: responseFormat !== 'default' ? responseFormat : undefined,
userProfileAbout: userProfileAbout !== '' ? userProfileAbout : undefined
});
dispatch('save');
};
</script>

<ManageModal bind:show={showManageModal} />

<form
id="tab-personalization"
class="flex flex-col h-full justify-between space-y-3 text-sm"
on:submit|preventDefault={saveHandler}
>
<div class="py-1 overflow-y-scroll max-h-[28rem] md:max-h-full">
<!-- Custom Instructions -->
<div class="mb-4">
<div class="text-sm font-medium mb-1" id="custom-instructions-label">
{$i18n.t('Custom Instructions')}
</div>
<div class="text-xs text-gray-600 dark:text-gray-400 mb-2">
{$i18n.t(
'Provide instructions that the AI should follow in every conversation. These are automatically included with each message you send.'
)}
</div>
<textarea
bind:value={customInstructions}
aria-labelledby="custom-instructions-label"
class="w-full text-sm bg-transparent outline-none resize-vertical rounded-xl p-3 outline outline-1 outline-gray-100 dark:outline-gray-800"
rows="3"
placeholder={$i18n.t(
'e.g., "Always provide code examples in Python. Explain concepts as if I\'m a senior developer."'
)}
/>
</div>

<hr class="border-gray-100/30 dark:border-gray-850/30 my-3" />

<!-- Response Preferences -->
<div class="mb-4">
<div class="text-sm font-medium mb-2">{$i18n.t('Response Preferences')}</div>

<!-- Tone -->
<div class="mb-3">
<div class="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
{$i18n.t('Tone')}
</div>
<div class="flex flex-wrap gap-2" role="radiogroup" aria-label={$i18n.t('Tone')}>
{#each [{ value: 'default', label: 'Default' }, { value: 'professional', label: 'Professional' }, { value: 'casual', label: 'Casual' }, { value: 'friendly', label: 'Friendly' }, { value: 'academic', label: 'Academic' }] as option}
<button
type="button"
role="radio"
aria-checked={responseTone === option.value}
class="px-3 py-1 text-xs rounded-full transition {responseTone === option.value
? 'bg-black text-white dark:bg-white dark:text-black'
: 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'}"
on:click={() => {
responseTone = option.value;
}}
>
{$i18n.t(option.label)}
</button>
{/each}
</div>
</div>

<!-- Verbosity -->
<div class="mb-3">
<div class="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
{$i18n.t('Verbosity')}
</div>
<div class="flex flex-wrap gap-2" role="radiogroup" aria-label={$i18n.t('Verbosity')}>
{#each [{ value: 'default', label: 'Default' }, { value: 'concise', label: 'Concise' }, { value: 'balanced', label: 'Balanced' }, { value: 'detailed', label: 'Detailed' }] as option}
<button
type="button"
role="radio"
aria-checked={responseVerbosity === option.value}
class="px-3 py-1 text-xs rounded-full transition {responseVerbosity ===
option.value
? 'bg-black text-white dark:bg-white dark:text-black'
: 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'}"
on:click={() => {
responseVerbosity = option.value;
}}
>
{$i18n.t(option.label)}
</button>
{/each}
</div>
</div>

<!-- Format -->
<div class="mb-3">
<div class="text-xs font-medium text-gray-700 dark:text-gray-300 mb-1">
{$i18n.t('Response Format')}
</div>
<div
class="flex flex-wrap gap-2"
role="radiogroup"
aria-label={$i18n.t('Response Format')}
>
{#each [{ value: 'default', label: 'Default' }, { value: 'markdown', label: 'Markdown' }, { value: 'plain', label: 'Plain Text' }, { value: 'structured', label: 'Structured' }] as option}
<button
type="button"
role="radio"
aria-checked={responseFormat === option.value}
class="px-3 py-1 text-xs rounded-full transition {responseFormat === option.value
? 'bg-black text-white dark:bg-white dark:text-black'
: 'bg-gray-100 dark:bg-gray-800 hover:bg-gray-200 dark:hover:bg-gray-700'}"
on:click={() => {
responseFormat = option.value;
}}
>
{$i18n.t(option.label)}
</button>
{/each}
</div>
</div>
</div>

<hr class="border-gray-100/30 dark:border-gray-850/30 my-3" />

<!-- About Me -->
<div class="mb-4">
<div class="text-sm font-medium mb-1" id="about-me-label">{$i18n.t('About Me')}</div>
<div class="text-xs text-gray-600 dark:text-gray-400 mb-2">
{$i18n.t(
'Share context about yourself so the AI can tailor its responses. This information is included as context in your conversations.'
)}
</div>
<textarea
bind:value={userProfileAbout}
aria-labelledby="about-me-label"
class="w-full text-sm bg-transparent outline-none resize-vertical rounded-xl p-3 outline outline-1 outline-gray-100 dark:outline-gray-800"
rows="3"
placeholder={$i18n.t(
'e.g., "I\'m a software engineer specializing in backend development. I work with Python and Go."'
)}
/>
</div>

{#if $config?.features?.enable_memories && ($user?.role === 'admin' || ($user?.permissions?.features?.memories ?? true))}
<hr class="border-gray-100/30 dark:border-gray-850/30 my-3" />

<!-- Memory Section -->
<div>
<div class="flex items-center justify-between mb-1">
<Tooltip
content={$i18n.t(
'This is an experimental feature, it may not function as expected and is subject to change at any time.'
)}
>
<div class="text-sm font-medium">
{$i18n.t('Memory')}

<span class=" text-xs text-gray-500">({$i18n.t('Experimental')})</span>
</div>
</Tooltip>

<div class="">
<Switch
bind:state={enableMemory}
on:change={async () => {
saveSettings({ memory: enableMemory });
}}
/>
</div>
</div>
</div>

<div class="text-xs text-gray-600 dark:text-gray-400">
<div>
{$i18n.t(
"You can personalize your interactions with LLMs by adding memories through the 'Manage' button below, making them more helpful and tailored to you."
)}
</div>
</div>

<div class="mt-3 mb-1 ml-1">
<button
type="button"
class=" px-3.5 py-1.5 font-medium hover:bg-black/5 dark:hover:bg-white/5 outline outline-1 outline-gray-300 dark:outline-gray-800 rounded-3xl"
on:click={() => {
showManageModal = true;
}}
>
{$i18n.t('Manage')}
</button>
</div>
{/if}
</div>

<div class="flex justify-end text-sm font-medium">
<button
class="px-3.5 py-1.5 text-sm font-medium bg-black hover:bg-gray-900 text-white dark:bg-white dark:text-black dark:hover:bg-gray-100 transition rounded-full"
type="submit"
>
{$i18n.t('Save')}
</button>
</div>
</form>
