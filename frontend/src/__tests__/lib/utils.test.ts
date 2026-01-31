import { describe, it, expect } from 'vitest'
import { cn } from '../../lib/utils'

describe('utils', () => {
  describe('cn', () => {
    it('複数のクラス名をマージできる', () => {
      const result = cn('class1', 'class2')
      expect(result).toBe('class1 class2')
    })

    it('条件付きクラス名を処理できる', () => {
      const result = cn('base', { active: true, disabled: false })
      expect(result).toBe('base active')
    })

    it('tailwindクラスの競合を解決できる', () => {
      const result = cn('px-2', 'px-4')
      expect(result).toBe('px-4')
    })

    it('空の入力を処理できる', () => {
      const result = cn()
      expect(result).toBe('')
    })

    it('undefinedやnullを処理できる', () => {
      const result = cn('base', undefined, null, 'extra')
      expect(result).toBe('base extra')
    })
  })
})
