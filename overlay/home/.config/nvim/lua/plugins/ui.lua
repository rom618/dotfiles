return {
  "tpope/vim-sensible",
  {
    "folke/tokyonight.nvim",
    lazy = false,
    priority = 1000,
    config = function()
      -- transparent so the terminal's translucent background shows through
      require("tokyonight").setup({ transparent = true })
      vim.cmd.colorscheme("tokyonight")
    end,
  },
  {
    "nvim-tree/nvim-tree.lua",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    keys = {
      { "<leader>e", "<cmd>NvimTreeToggle<cr>", desc = "Toggle file explorer" },
    },
    lazy = false,
    config = function()
      require("nvim-tree").setup()
    end,
  },
  "tpope/vim-fugitive",
  {
    "lewis6991/gitsigns.nvim",
    config = function()
      require("gitsigns").setup()
    end,
  },
  {
    "nvim-lualine/lualine.nvim",
    dependencies = { "nvim-tree/nvim-web-devicons" },
    config = function()
      require("lualine").setup({ options = { theme = "auto" } })
    end,
  },
  {
    "windwp/nvim-autopairs",
    event = "InsertEnter",
    config = function()
      require("nvim-autopairs").setup()
    end,
  },
  {
    "folke/which-key.nvim",
    event = "VeryLazy",
    opts = {
      spec = {
        { "<leader>c", group = "Code" },
        { "<leader>f", group = "Find (Telescope)" },
        { "<leader>l", group = "LSP pickers" },
        { "<leader>v", group = "Visual" },
        { "<leader>x", group = "Trouble lists" },
        { "gr", group = "LSP (built-in)" },
      },
    },
  },
}
