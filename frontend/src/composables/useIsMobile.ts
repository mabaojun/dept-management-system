import { onMounted, onUnmounted, ref } from 'vue'

/** 移动端检测：视口宽 < 768px 视为手机/窄屏 */
export function useIsMobile() {
  const isMobile = ref(window.innerWidth < 768)

  function update() {
    isMobile.value = window.innerWidth < 768
  }

  onMounted(() => window.addEventListener('resize', update))
  onUnmounted(() => window.removeEventListener('resize', update))

  return { isMobile }
}
