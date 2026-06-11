<script lang="ts">
  import { onMount, onDestroy } from 'svelte';
  import { connect, disconnect, send } from '$lib/websocket.js';
  import { posture, monitoring, settings, history, wsState } from '$lib/stores.svelte.js';
  import StatusCard from '$lib/components/StatusCard.svelte';
  import HistoryBar from '$lib/components/HistoryBar.svelte';
  import SettingsPanel from '$lib/components/SettingsPanel.svelte';
  import VideoFeed from '$lib/components/VideoFeed.svelte';

  let showSettings = $state(false);
  let showVideo = $state(false);

  onMount(() => { connect(); });
  onDestroy(() => { disconnect(); });

  function toggleMonitoring() {
    const next = !monitoring.active;
    monitoring.active = next;
    send({ type: next ? 'start' : 'stop' });
  }

  function calibrate() {
    send({ type: 'calibrate' });
  }

  const wsColor = $derived(() => ({
    connecting: 'bg-yellow-500',
    open:       'bg-green-500',
    closed:     'bg-slate-500',
    error:      'bg-red-500'
  }[wsState.current] ?? 'bg-slate-500'));

  const goodPct = $derived(() => {
    if (history.length === 0) return 0;
    const good = history.filter(e => e.status === 'good').length;
    return Math.round((good / history.length) * 100);
  });
</script>

<!-- Header -->
<header class="sticky top-0 z-30 border-b border-slate-800/80 bg-slate-950/90 backdrop-blur-md">
  <div class="max-w-3xl mx-auto flex items-center justify-between px-4 py-3">
    <div class="flex items-center gap-3">
      <span class="text-xl">🧍</span>
      <span class="font-semibold text-slate-100 tracking-tight">PostureMonitor</span>
    </div>
    <div class="flex items-center gap-3">
      <!-- WS status dot -->
      <span title="Connection: {wsState.current}" class={`w-2 h-2 rounded-full ${wsColor()} animate-pulse`}></span>
      <button
        onclick={() => showSettings = true}
        class="p-2 rounded-xl text-slate-400 hover:text-white hover:bg-slate-800 transition-all"
        title="Settings"
      >
        ⚙️
      </button>
    </div>
  </div>
</header>

<!-- Main -->
<main class="max-w-3xl mx-auto px-4 py-8 space-y-6">

  <!-- Status card -->
  <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-8">
    <StatusCard
      status={posture.status}
      confidence={posture.confidence}
      message={posture.message}
      issues={posture.issues}
      monitoring={monitoring.active}
    />
  </div>

  <!-- Score summary + controls row -->
  <div class="grid grid-cols-2 gap-4">
    <!-- Good posture % -->
    <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 text-center">
      <p class="text-3xl font-bold text-green-400">{goodPct()}%</p>
      <p class="text-slate-500 text-xs mt-1">Good posture<br/>this session</p>
    </div>

    <!-- Quick controls -->
    <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-5 flex flex-col gap-3">
      <button
        onclick={toggleMonitoring}
        class={`py-2 rounded-xl text-sm font-semibold transition-all shadow-lg
          ${monitoring.active
            ? 'bg-green-600 hover:bg-green-500 text-white shadow-green-500/20'
            : 'bg-slate-700 hover:bg-slate-600 text-slate-300'}`}
      >
        {monitoring.active ? '⏸ Pause' : '▶ Start'} Monitoring
      </button>
      <button
        onclick={calibrate}
        class="py-2 rounded-xl text-sm font-medium bg-slate-700 hover:bg-slate-600 text-slate-300 transition-all"
      >
        📐 Calibrate
      </button>
    </div>
  </div>

  <!-- History -->
  <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
    <HistoryBar history={history} />
  </div>

  <!-- Camera preview (toggle) -->
  <div class="bg-slate-900/60 border border-slate-800 rounded-2xl p-5">
    <button
      onclick={() => showVideo = !showVideo}
      class="flex items-center justify-between w-full text-slate-300 hover:text-white transition-colors text-sm font-medium"
    >
      <span>📷 Camera preview</span>
      <span class="text-slate-500">{showVideo ? '▲ hide' : '▼ show'}</span>
    </button>
    {#if showVideo}
      <div class="mt-4">
        <VideoFeed visible={showVideo} />
      </div>
    {/if}
  </div>

  <!-- Sensitivity chip row -->
  <div class="flex items-center justify-center gap-2 text-xs text-slate-500">
    <span>Sensitivity:</span>
    <span class="px-2 py-0.5 bg-slate-800 rounded-full capitalize text-slate-300">{settings.sensitivity}</span>
    <span>·</span>
    <span>Language:</span>
    <span class="px-2 py-0.5 bg-slate-800 rounded-full uppercase text-slate-300">{settings.language}</span>
    <button
      onclick={() => showSettings = true}
      class="text-blue-400 hover:text-blue-300 underline"
    >Edit</button>
  </div>

</main>

{#if showSettings}
  <SettingsPanel settings={settings} onclose={() => showSettings = false} />
{/if}
