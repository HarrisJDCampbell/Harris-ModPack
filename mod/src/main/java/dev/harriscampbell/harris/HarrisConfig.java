package dev.harriscampbell.harris;

import net.neoforged.neoforge.common.ModConfigSpec;

/** config/harris-common.toml */
public final class HarrisConfig {
    private static final ModConfigSpec.Builder BUILDER = new ModConfigSpec.Builder();

    public static final ModConfigSpec.BooleanValue CONFETTI_CREEPERS = BUILDER
            .comment("Creepers explode into confetti instead of blowing up blocks and players.")
            .define("confettiCreepers", true);

    public static final ModConfigSpec.IntValue CONFETTI_AMOUNT = BUILDER
            .comment("Confetti pieces per creeper (charged creepers throw twice as many).")
            .defineInRange("confettiAmount", 180, 10, 1000);

    public static final ModConfigSpec SPEC = BUILDER.build();

    private HarrisConfig() {}
}
