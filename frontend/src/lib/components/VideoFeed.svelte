<script lang="ts">
  interface Props {
    visible: boolean;
  }
  let { visible }: Props = $props();

  const src = '/video_feed';
</script>

{#if visible}
  <div class="relative rounded-2xl overflow-hidden border border-slate-700 bg-slate-900 aspect-video">
    <img
      {src}
      alt="Camera feed"
      class="w-full h-full object-cover"
    />
    <span class="absolute top-2 left-2 bg-black/60 text-xs text-red-400 px-2 py-0.5 rounded-full font-medium">
      ● LIVE
    </span>
  </div>
{/if}
