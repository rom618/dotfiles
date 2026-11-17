-- repo overrides (trusted .nvim.lua): vim.g.format_on_save = false|true, vim.g.formatters_by_ft = { php = { "php_cs_fixer" } }

local prettier_files = {
  ".prettierrc", ".prettierrc.json", ".prettierrc.json5", ".prettierrc.yaml", ".prettierrc.yml",
  ".prettierrc.toml", ".prettierrc.js", ".prettierrc.cjs", ".prettierrc.mjs", ".prettierrc.ts",
  ".prettierrc.cts", ".prettierrc.mts", "prettier.config.js", "prettier.config.cjs",
  "prettier.config.mjs", "prettier.config.ts", "prettier.config.cts", "prettier.config.mts",
}
local prettier_fts = {
  "javascript", "javascriptreact", "typescript", "typescriptreact", "vue",
  "css", "scss", "less", "html", "json", "jsonc", "yaml", "markdown", "graphql",
}

local function find_up(bufnr, names)
  local name = vim.api.nvim_buf_get_name(bufnr)
  local dir = name ~= "" and vim.fs.dirname(name) or vim.uv.cwd()
  return vim.fs.find(names, { upward = true, path = dir })[1]
end

local function has(bufnr, names)
  return find_up(bufnr, names) ~= nil
end

local function package_json_has_prettier(bufnr)
  local path = find_up(bufnr, { "package.json" })
  if not path then
    return false
  end
  return vim.json.decode(table.concat(vim.fn.readfile(path), "\n")).prettier ~= nil
end

local function pyproject_has_ruff(bufnr)
  local path = find_up(bufnr, { "pyproject.toml" })
  if not path then
    return false
  end
  for _, line in ipairs(vim.fn.readfile(path)) do
    if line:match("^%s*%[tool%.ruff[%].]") then
      return true
    end
  end
  return false
end

local configured = {
  php = function(b)
    if has(b, { "pint.json" }) then
      return { "pint" }
    end
    if has(b, { ".php-cs-fixer.php", ".php-cs-fixer.dist.php" }) then
      return { "php_cs_fixer" }
    end
  end,
  python = function(b)
    if has(b, { "ruff.toml", ".ruff.toml" }) or pyproject_has_ruff(b) then
      return { "ruff_format" }
    end
  end,
  lua = function(b)
    if has(b, { "stylua.toml", ".stylua.toml" }) then
      return { "stylua" }
    end
  end,
  rust = function(b)
    if has(b, { "rustfmt.toml", ".rustfmt.toml", "Cargo.toml" }) then
      return { "rustfmt" }
    end
  end,
}
for _, ft in ipairs(prettier_fts) do
  configured[ft] = function(b)
    if has(b, prettier_files) or package_json_has_prettier(b) then
      return { "prettier" }
    end
  end
end

local manual = {
  php = function(b)
    if has(b, { "vendor/bin/pint" }) then
      return { "pint" }
    end
    if has(b, { "vendor/bin/php-cs-fixer" }) then
      return { "php_cs_fixer" }
    end
    return {}
  end,
  python = { "ruff_format" },
  lua = { "stylua" },
  rust = { "rustfmt" },
  sh = { "shfmt" },
  bash = { "shfmt" },
}
for _, ft in ipairs(prettier_fts) do
  manual[ft] = { "prettier" }
end

local function override(bufnr, ft)
  local t = vim.b[bufnr].formatters_by_ft or vim.g.formatters_by_ft
  return t and t[ft]
end

local function from_config(bufnr, ft)
  return override(bufnr, ft) or (configured[ft] and configured[ft](bufnr))
end

local function formatters_for(bufnr, ft)
  local chosen = from_config(bufnr, ft)
  if chosen then
    return chosen
  end
  local m = manual[ft]
  if type(m) == "function" then
    return m(bufnr)
  end
  return m or {}
end

local formatters_by_ft = {}
for ft in pairs(vim.tbl_extend("force", {}, configured, manual)) do
  formatters_by_ft[ft] = function(bufnr)
    return formatters_for(bufnr, ft)
  end
end

local function format_on_save(bufnr)
  local flag = vim.b[bufnr].format_on_save
  if flag == nil then
    flag = vim.g.format_on_save
  end
  if flag == false then
    return nil
  end
  local ft = vim.bo[bufnr].filetype
  if flag == true or from_config(bufnr, ft) then
    return { timeout_ms = 3000, lsp_format = "fallback" }
  end
end

return {
  {
    "stevearc/conform.nvim",
    event = "BufWritePre",
    cmd = "ConformInfo",
    keys = {
      {
        "<leader>cf",
        function()
          require("conform").format({ async = true, lsp_format = "fallback" })
        end,
        mode = { "n", "x" },
        desc = "Format buffer / selection",
      },
    },
    opts = {
      formatters_by_ft = formatters_by_ft,
      format_on_save = format_on_save,
    },
    config = function(_, opts)
      -- pint reads pint.json from its working directory
      opts.formatters = { pint = { cwd = require("conform.util").root_file({ "pint.json", "composer.json" }) } }
      require("conform").setup(opts)
    end,
  },
}
