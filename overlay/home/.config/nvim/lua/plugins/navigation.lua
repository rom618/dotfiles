local function telescope(picker)
  return function()
    require("telescope.builtin")[picker]()
  end
end

return {
  {
    "nvim-telescope/telescope.nvim",
    cmd = "Telescope",
    dependencies = {
      "nvim-lua/plenary.nvim",
      { "nvim-telescope/telescope-fzf-native.nvim", build = "make" },
    },
    keys = {
      { "<leader>ff", telescope("find_files"), desc = "Find files" },
      { "<leader>fg", telescope("live_grep"), desc = "Live grep" },
      { "<leader>fb", telescope("buffers"), desc = "Buffers" },
      { "<leader>lr", telescope("lsp_references"), desc = "References" },
      { "<leader>ls", telescope("lsp_document_symbols"), desc = "Document symbols" },
      { "<leader>lS", telescope("lsp_dynamic_workspace_symbols"), desc = "Workspace symbols" },
    },
    config = function()
      require("telescope").setup({})
      require("telescope").load_extension("fzf")
    end,
  },
  {
    "folke/trouble.nvim",
    cmd = "Trouble",
    opts = {},
    keys = {
      { "<leader>xx", "<cmd>Trouble diagnostics toggle<cr>", desc = "Diagnostics (workspace)" },
      { "<leader>xX", "<cmd>Trouble diagnostics toggle filter.buf=0<cr>", desc = "Diagnostics (buffer)" },
      { "<leader>xr", "<cmd>Trouble lsp toggle focus=false win.position=right<cr>", desc = "LSP definitions / references" },
      { "<leader>xs", "<cmd>Trouble symbols toggle focus=false<cr>", desc = "Symbols outline" },
      { "<leader>xq", "<cmd>Trouble qflist toggle<cr>", desc = "Quickfix list" },
    },
  },
}
