import { describe, it, expect, afterEach } from 'vitest'
import { render, screen, cleanup } from '@testing-library/react'
import App from '../App'

describe('App', () => {
  afterEach(() => {
    cleanup()
  })

  it('マウントできる', () => {
    render(<App />)
    // 最小限の確認: エラーなくレンダリングされる
    expect(document.body).toBeTruthy()
  })

  it('BI Toolというテキストが表示される', () => {
    render(<App />)
    expect(screen.getByText('BI Tool')).toBeInTheDocument()
  })
})
