import { onBeforeUnmount, onMounted } from 'vue'

/**
 * Add a class="reveal" to any element you want to animate on scroll.
 * Mount this composable once in any view; it observes all .reveal nodes.
 *
 *   <script setup>
 *     import { useReveal } from '@/composables/useReveal'
 *     useReveal()
 *   </script>
 *   <div class="reveal">Fades in when scrolled into view</div>
 */
export function useReveal(options = {}) {
  let io = null

  onMounted(() => {
    if (typeof window === 'undefined' || !('IntersectionObserver' in window)) {
      // Fallback: just show everything
      document.querySelectorAll('.reveal').forEach((el) => el.classList.add('visible'))
      return
    }
    io = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (entry.isIntersecting) {
            entry.target.classList.add('visible')
            io.unobserve(entry.target)
          }
        }
      },
      { threshold: options.threshold ?? 0.12, rootMargin: options.rootMargin ?? '0px 0px -10% 0px' },
    )
    document.querySelectorAll('.reveal').forEach((el) => io.observe(el))
  })

  onBeforeUnmount(() => { if (io) io.disconnect() })
}
