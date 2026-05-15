# Nexus Comment Draft: Epic / Game Pass Support

Thanks for testing and reporting the folder layouts.

I pushed patch `0.1.1` to improve non-Steam installs:

- Steam is still the only auto-detected/tested storefront.
- Epic/manual Win64 installs should now work through Settings -> Browse Install if the folder has the normal Unreal layout with the shipping exe and `Content\Paks`.
- You can select the outer install folder, inner `Subnautica2` folder, or `Subnautica2\Binaries\Win64`.
- Game Pass WinGDK is now detected experimentally for the reported layout:
  `Content\Subnautica2\Binaries\WinGDK`

For Game Pass, the manager now follows the ProtonLabs package notes: the Game Pass UE4SS base is treated as a Content-root runtime payload, while standard Lua mods target `Content\Subnautica2\Binaries\WinGDK\ue4ss\Mods` when the WinGDK layout is detected. Runtime packages are still shown in Preview & Apply so you can verify every file target before applying.

This is still marked experimental because some mods may crash on Game Pass/WinGDK even when installed to the correct folder. If the game crashes after loading a save, test one mod at a time and send a support report from Help / About / Support.

Loose root overlays and unsafe unmanaged writes are still blocked by policy.
