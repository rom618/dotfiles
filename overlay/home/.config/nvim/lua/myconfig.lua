vim.g.mapleader = " "
vim.g.maplocalleader = " "

local lazypath = vim.fn.stdpath("data") .. "/lazy/lazy.nvim"
if not vim.uv.fs_stat(lazypath) then
  vim.fn.system({
    "git",
    "clone",
    "--filter=blob:none",
    "https://github.com/folke/lazy.nvim.git",
    lazypath,
  })
end
vim.opt.rtp:prepend(lazypath)

vim.opt.number = true
vim.opt.relativenumber = true
vim.opt.tabstop = 4
vim.opt.shiftwidth = 4
vim.opt.expandtab = true
vim.opt.smartindent = true
vim.opt.clipboard = "unnamedplus"
vim.o.termguicolors = true
-- project .nvim.lua files (cwd and parents) run only after :trust
vim.o.exrc = true

vim.diagnostic.config({
  severity_sort = true,
  underline = true,
  signs = true,
  virtual_text = { spacing = 2, source = "if_many" },
  float = { border = "rounded", source = true },
})

require("lazy").setup({
  spec = { { import = "plugins" } },
  install = { colorscheme = { "tokyonight" } },
})

vim.keymap.set("n", "<leader>vb", "<C-v>", { desc = "enter visual block mode" })
