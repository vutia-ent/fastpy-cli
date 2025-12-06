import { defineConfig } from 'vitepress'

export default defineConfig({
  title: 'Fastpy CLI',
  description: 'Create production-ready FastAPI projects with one command',

  head: [
    ['link', { rel: 'icon', href: '/logo.svg' }],
  ],

  themeConfig: {
    logo: '/logo.svg',

    nav: [
      { text: 'Guide', link: '/guide/quick-start' },
      { text: 'Commands', link: '/guide/commands' },
      { text: 'Libs', link: '/guide/libs' },
      { text: 'GitHub', link: 'https://github.com/vutia-ent/fastpy-cli' }
    ],

    sidebar: [
      {
        text: 'Getting Started',
        items: [
          { text: 'Installation', link: '/guide/installation' },
          { text: 'Quick Start', link: '/guide/quick-start' },
        ]
      },
      {
        text: 'Reference',
        items: [
          { text: 'Commands', link: '/guide/commands' },
          { text: 'Configuration', link: '/guide/configuration' },
          { text: 'AI Generation', link: '/guide/ai' },
        ]
      },
      {
        text: 'Libs',
        items: [
          { text: 'Overview', link: '/guide/libs' },
          { text: 'Http', link: '/guide/libs/http' },
          { text: 'Mail', link: '/guide/libs/mail' },
          { text: 'Cache', link: '/guide/libs/cache' },
          { text: 'Storage', link: '/guide/libs/storage' },
          { text: 'Queue', link: '/guide/libs/queue' },
          { text: 'Events', link: '/guide/libs/events' },
          { text: 'Notifications', link: '/guide/libs/notifications' },
          { text: 'Hash', link: '/guide/libs/hash' },
          { text: 'Crypt', link: '/guide/libs/crypt' },
        ]
      }
    ],

    socialLinks: [
      { icon: 'github', link: 'https://github.com/vutia-ent/fastpy-cli' }
    ],

    footer: {
      message: 'Released under the MIT License.',
      copyright: 'Copyright © 2024 Vutia Enterprise'
    },

    search: {
      provider: 'local'
    }
  }
})
