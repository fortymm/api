defmodule FortymmApi.Repo.Migrations.CreateUsersAuthTables do
  use Ecto.Migration

  def change do
    execute "CREATE EXTENSION IF NOT EXISTS citext", ""

    create table(:users) do
      add :username, :string, null: false
      add :email, :citext
      add :hashed_password, :string
      add :confirmed_at, :utc_datetime

      timestamps(type: :utc_datetime)
    end

    # Email unique only when present (allows multiple NULLs)
    create unique_index(:users, [:email], where: "email IS NOT NULL")

    # Username case-insensitive uniqueness
    create unique_index(:users, ["lower(username)"], name: :users_username_lower_index)

    create table(:users_tokens) do
      add :user_id, references(:users, on_delete: :delete_all), null: false
      add :token, :binary, null: false
      add :context, :string, null: false
      add :sent_to, :string
      add :authenticated_at, :utc_datetime

      timestamps(type: :utc_datetime, updated_at: false)
    end

    create index(:users_tokens, [:user_id])
    create unique_index(:users_tokens, [:context, :token])
  end
end
