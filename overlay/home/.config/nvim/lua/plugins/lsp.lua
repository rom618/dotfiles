local servers = {
  "intelephense",
  "vtsls",
  "vue_ls",
  "basedpyright",
  "ruff",
  "lua_ls",
  "bashls",
  "marksman",
  "rust_analyzer",
}

return {
  {
    "mason-org/mason.nvim",
    lazy = false,
    opts = {},
  },
  {
    "WhoIsSethDaniel/mason-tool-installer.nvim",
    dependencies = { "mason-org/mason.nvim" },
    lazy = false,
    opts = {
      ensure_installed = {
        "intelephense",
        "vue-language-server",
        "vtsls",
        "basedpyright",
        "ruff",
        "lua-language-server",
        "bash-language-server",
        "marksman",
        "rust-analyzer",
        "prettier",
        "stylua",
        "shfmt",
        "php-cs-fixer",
        "tree-sitter-cli",
      },
    },
  },
  {
    "folke/lazydev.nvim",
    ft = "lua",
    opts = {
      library = {
        { path = "${3rd}/luv/library", words = { "vim%.uv" } },
      },
    },
  },
  {
    "neovim/nvim-lspconfig",
    event = { "BufReadPre", "BufNewFile" },
    dependencies = { "mason-org/mason.nvim", "saghen/blink.cmp" },
    config = function()
      vim.lsp.config("*", { capabilities = require("blink.cmp").get_lsp_capabilities() })

      local vue_plugin = {
        name = "@vue/typescript-plugin",
        location = vim.fn.expand("$MASON/packages/vue-language-server/node_modules/@vue/language-server"),
        languages = { "vue" },
        configNamespace = "typescript",
      }
      vim.lsp.config("vtsls", {
        settings = { vtsls = { tsserver = { globalPlugins = { vue_plugin } } } },
        filetypes = { "typescript", "javascript", "javascriptreact", "typescriptreact", "vue" },
      })

      vim.api.nvim_create_autocmd("LspAttach", {
        group = vim.api.nvim_create_augroup("myconfig_lsp", { clear = true }),
        callback = function(args)
          local client = assert(vim.lsp.get_client_by_id(args.data.client_id))
          -- basedpyright answers hover for Python, ruff would duplicate it
          if client.name == "ruff" then
            client.server_capabilities.hoverProvider = false
          end
          local function map(lhs, rhs, desc)
            vim.keymap.set("n", lhs, rhs, { buffer = args.buf, desc = desc })
          end
          map("gd", vim.lsp.buf.definition, "Go to definition")
          map("gD", vim.lsp.buf.declaration, "Go to declaration")
        end,
      })

      vim.lsp.enable(servers)
    end,
  },
}
