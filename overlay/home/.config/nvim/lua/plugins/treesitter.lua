local parsers = {
  "asm", "bash", "c", "cpp", "css", "html", "javascript", "json", "lua",
  "markdown", "markdown_inline", "php", "phpdoc", "python", "rust", "sql",
  "twig", "typescript", "vim", "vimdoc", "vue", "yaml",
}

local function select(capture)
  return function()
    require("nvim-treesitter-textobjects.select").select_textobject(capture, "textobjects")
  end
end

local function move(fn, capture, native)
  return function()
    -- keep ]c / [c for diff hunks in diff mode
    if native and vim.wo.diff then
      vim.cmd.normal({ vim.v.count1 .. native, bang = true })
      return
    end
    require("nvim-treesitter-textobjects.move")[fn](capture, "textobjects")
  end
end

return {
  {
    "nvim-treesitter/nvim-treesitter",
    branch = "main",
    lazy = false,
    build = ":TSUpdate",
    dependencies = { "mason-org/mason.nvim" },
    config = function()
      require("nvim-treesitter").install(parsers)
      vim.api.nvim_create_autocmd("FileType", {
        group = vim.api.nvim_create_augroup("myconfig_treesitter", { clear = true }),
        callback = function(args)
          local lang = vim.treesitter.language.get_lang(args.match)
          if lang and vim.treesitter.language.add(lang) then
            vim.treesitter.start(args.buf, lang)
            vim.bo[args.buf].indentexpr = "v:lua.require'nvim-treesitter'.indentexpr()"
          end
        end,
      })
    end,
  },
  {
    "nvim-treesitter/nvim-treesitter-textobjects",
    branch = "main",
    event = { "BufReadPost", "BufNewFile" },
    config = function()
      require("nvim-treesitter-textobjects").setup({
        select = { lookahead = true },
        move = { set_jumps = true },
      })
      local map = vim.keymap.set
      map({ "x", "o" }, "af", select("@function.outer"), { desc = "around function" })
      map({ "x", "o" }, "if", select("@function.inner"), { desc = "inside function" })
      map({ "x", "o" }, "ac", select("@class.outer"), { desc = "around class" })
      map({ "x", "o" }, "ic", select("@class.inner"), { desc = "inside class" })
      map({ "n", "x", "o" }, "]f", move("goto_next_start", "@function.outer"), { desc = "Next function" })
      map({ "n", "x", "o" }, "[f", move("goto_previous_start", "@function.outer"), { desc = "Previous function" })
      map({ "n", "x", "o" }, "]c", move("goto_next_start", "@class.outer", "]c"), { desc = "Next class (diff: next change)" })
      map({ "n", "x", "o" }, "[c", move("goto_previous_start", "@class.outer", "[c"), { desc = "Previous class (diff: previous change)" })
    end,
  },
}
