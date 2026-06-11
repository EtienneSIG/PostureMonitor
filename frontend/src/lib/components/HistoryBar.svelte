<script lang="ts">
  import type { PostureEntry } from '$lib/stores.svelte.js';

  interface Props {
    history: PostureEntry[];
  }
  let { history }: Props = $props();

  function color(status: string) {
    switch (status) {
      case 'good': return 'bg-green-500';
      case 'fair': return 'bg-amber-500';
      case 'poor': return 'bg-red-500';
      default:     return 'bg-slate-600';
    }
  }

  function fmt(ts: number) {
    return new Date(ts).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  }
</script>

<div class="space-y-3">
  <h3 class="text-slate-400 text-xs uppercase tracking-widest font-semibold">Recent history</h3>

  {#if history.length === 0}
    <p class="text-slate-600 text-sm">No data yet — start monitoring to see history.</p>
  {:else}
    <!-- Mini bar chart -->
    <div class="flex items-end gap-0.5 h-10">
      {#each history.slice(0, 60).toReversed() as entry}
        <div
          class={`flex-1 rounded-sm min-w-0 transition-all duration-300 ${color(entry.status)}`}
          style="height: {Math.max(20, entry.confidence)}%"
          title="{entry.status} — {fmt(entry.timestamp)}"
        ></div>
      {/each}
    </div>

    <!-- Last 5 text entries -->
    <ul class="space-y-1">
      {#each history.slice(0, 5) as entry}
        <li class="flex items-center justify-between text-xs text-slate-400">
          <span class={`font-medium ${color(entry.status).replace('bg-', 'text-')}`}>{entry.status}</span>
          <span class="truncate mx-2 text-slate-500">{entry.message}</span>
          <span class="shrink-0 text-slate-600">{fmt(entry.timestamp)}</span>
        </li>
      {/each}
    </ul>
  {/if}
</div>
