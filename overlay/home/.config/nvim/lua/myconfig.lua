-- Bootstrap lazy.nvim
local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.loop.fs_stat(lazypath) then
  vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

-- Basic settings
vim.opt.number = true          -- Show line numbers
vim.opt.relativenumber = true  -- Relative line numbers
vim.opt.tabstop = 4            -- Tab width
vim.opt.shiftwidth = 4         -- Indent width
vim.opt.expandtab = true       -- Use spaces instead of tabs
vim.opt.smartindent = true     -- Smart auto-indenting
vim.opt.clipboard = "unnamedplus" -- Use system clipboard

require("lazy").setup({
  -- Essential plugins
  "tpope/vim-sensible",
    "folke/tokyonight.nvim",
  
  -- Better syntax highlighting
  { 
    "nvim-treesitter/nvim-treesitter", 
    build = ":TSUpdate",
    config = function()
      require("nvim-treesitter.configs").setup({
        -- Add languages you use here
        ensure_installed = { 
          "c", "cpp", "lua", "vim", "vimdoc",
          "python", "javascript", "typescript",
          "html", "css", "json", "yaml",
          "bash", "markdown", "asm"
        },
        highlight = { enable = true },
        indent = { enable = true },
      })
    end
  },
  
  -- Fuzzy finder (requires plenary)
  {
    "nvim-telescope/telescope.nvim",
    dependencies = { "nvim-lua/plenary.nvim" },
  },
  
  -- LSP support
  {
    "neovim/nvim-lspconfig",
    config = function()
      -- Setup LSP servers here if needed
      -- Example: require("lspconfig").pyright.setup{}
    end
  },
  
  -- Autocompletion
  {
    "hrsh7th/nvim-cmp",
    dependencies = {
      "hrsh7th/cmp-nvim-lsp",
      "hrsh7th/cmp-buffer",
      "hrsh7th/cmp-path",
    },
    config = function()
      local cmp = require("cmp")
      cmp.setup({
        mapping = cmp.mapping.preset.insert({
          ["<C-Space>"] = cmp.mapping.complete(),
          ["<CR>"] = cmp.mapping.confirm({ select = true }),
          ["<Tab>"] = cmp.mapping.select_next_item(),
          ["<S-Tab>"] = cmp.mapping.select_prev_item(),
        }),
        sources = {
          { name = "nvim_lsp" },
          { name = "buffer" },
          { name = "path" },
        },
      })
    end
  },
  
  -- Assembly syntax (optional, remove if not needed)
  -- "jrozner/vim-asm",
  
  -- File explorer
  {
    "nvim-tree/nvim-tree.lua",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    config = function()
      require("nvim-tree").setup()
    end
  },
  
  -- Git integration
  "tpope/vim-fugitive",
  {
    "lewis6991/gitsigns.nvim",
    config = function()
      require("gitsigns").setup()
    end
  },
  
  -- Status line
  {
    "nvim-lualine/lualine.nvim",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    config = function()
      require("lualine").setup({
        options = { theme = "auto" }
      })
    end
  },
  
  -- Auto-pairs (automatically close brackets, quotes, etc)
  {
    "windwp/nvim-autopairs",
    config = function()
      require("nvim-autopairs").setup()
    end
  },
  
  -- Comment toggling (gcc to comment line, gc in visual mode)
  {
    "numToStr/Comment.nvim",
    config = function()
      require("Comment").setup()
    end
  },
  
  -- Color scheme (optional - uncomment to use)
  -- { "catppuccin/nvim", name = "catppuccin", priority = 1000 },
  -- { "folke/tokyonight.nvim", priority = 1000 },
})

-- Key mappings for word movement
-- In normal mode:
-- w = move forward to start of next word
-- b = move backward to start of previous word
-- e = move forward to end of word
-- W, B, E = same but for WORD (space-separated)

-- Additional useful keybindings
vim.keymap.set("n", "<leader>ff", "<cmd>Telescope find_files<cr>", { desc = "Find files" })
vim.keymap.set("n", "<leader>fg", "<cmd>Telescope live_grep<cr>", { desc = "Live grep" })
vim.keymap.set("n", "<leader>fb", "<cmd>Telescope buffers<cr>", { desc = "Buffers" })
vim.keymap.set("n", "<leader>e", "<cmd>NvimTreeToggle<cr>", { desc = "Toggle file explorer" })

-- Set leader key (default is backslash, many prefer space)
vim.g.mapleader = " "
vim.g.maplocalleader = " "

-- enable true color
vim.o.termguicolors = true

-- set the colorscheme (must be after plugin is loaded)
-- transparent = true so the terminal's own (translucent) background shows
-- through instead of tokyonight's solid fill clashing with it
require("tokyonight").setup({
  transparent = true,
})
vim.cmd[[colorscheme tokyonight]]
-- vim.cmd.colorscheme("catppuccin")
vim.keymap.set("n", "<leader>vb", "<C-v>", { desc = "enter visual block mode" })
