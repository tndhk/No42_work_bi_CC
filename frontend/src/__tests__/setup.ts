import { expect, vi } from 'vitest'
import * as matchers from '@testing-library/jest-dom/matchers'

expect.extend(matchers)

// CSS imports mock (react-grid-layout, react-resizable)
vi.mock('react-grid-layout/css/styles.css', () => ({}))
vi.mock('react-resizable/css/styles.css', () => ({}))
