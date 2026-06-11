<script lang="ts">
  import type { PostureStatus } from '$lib/stores.svelte.js';

  interface Props {
    status: PostureStatus;
    confidence: number;
    message: string;
    issues: string[];
    monitoring: boolean;
  }

  let { status, confidence, message, issues, monitoring }: Props = $props();

  const config = $derived(() => {
    switch (status) {
      case 'good':
        return { label: 'Good Posture', emoji: '🟢', ring: 'ring-green-500', text: 'text-green-400', bg: 'bg-green-500/10', pct: confidence };
      case 'fair':
        return { label: 'Fair Posture', emoji: '🟡', ring: 'ring-amber-500', text: 'text-amber-400', bg: 'bg-amber-500/10', pct: confidence };
      case 'poor':
        return { label: 'Poor Posture', emoji: '🔴', ring: 'ring-red-500', text: 'text-red-400', bg: 'bg-red-500/10', pct: confidence };
      case 'disabled':
        return { label: 'Monitoring Off', emoji: '⏸', ring: 'ring-slate-500', text: 'text-slate-400', bg: 'bg-slate-500/10', pct: 0 };
      default:
        return { label: 'No Detection', emoji: '👤', ring: 'ring-slate-600', text: 'text-slate-400', bg: 'bg-slate-500/10', pct: 0 };
    }
  });

  const circumference = 2 * Math.PI * 54;
  const dashOffset = $derived(() => circumference * (1 - (config().pct / 100)));
</script>

<div class="flex flex-col items-center gap-6">
  <!-- Circular progress indicator -->
  <div class="relative">
    <svg width="136" height="136" class="-rotate-90">
      <circle cx="68" cy="68" r="54" fill="none" stroke="#1e293b" stroke-width="10" />
      <circle
        cx="68" cy="68" r="54" fill="none"
        stroke-width="10"
        stroke-linecap="round"
        class="transition-all duration-700"
        class:stroke-green-500={status === 'good'}
        class:stroke-amber-500={status === 'fair'}
        class:stroke-red-500={status === 'poor'}
        class:stroke-slate-600={status === 'no_detection' || status === 'disabled'}
        stroke-dasharray={circumference}
        stroke-dashoffset={dashOffset()}
      />
    </svg>
    <!-- emoji in the centre -->
    <span class="absolute inset-0 flex items-center justify-center text-5xl select-none">
      {config().emoji}
    </span>
  </div>

  <!-- Status label & message -->
  <div class="text-center space-y-1">
    <p class={`text-2xl font-bold ${config().text}`}>{config().label}</p>
    <p class="text-slate-400 text-sm">{message}</p>
    {#if config().pct > 0}
      <p class="text-slate-500 text-xs">Confidence {Math.round(config().pct)}%</p>
    {/if}
  </div>

  <!-- Issues list -->
  {#if issues.length > 0}
    <ul class={`w-full rounded-xl ${config().bg} border border-white/5 p-4 space-y-1`}>
      {#each issues as issue}
        <li class="flex items-center gap-2 text-sm text-slate-300">
          <span class="text-xs">⚠️</span> {issue}
        </li>
      {/each}
    </ul>
  {/if}

  <!-- Monitoring badge -->
  {#if !monitoring}
    <span class="px-3 py-1 rounded-full bg-slate-700/60 text-slate-400 text-xs font-medium">
      Monitoring paused
    </span>
  {/if}
</div>
